"""
╔══════════════════════════════════════════════════════════════╗
║         AI BEHAVIOR SYSTEM  ·  ai_behavior_system.py         ║
║  Behavior Trees · FSM · GOAP · A* Pathfinding · NPC Manager  ║
╚══════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations
import asyncio, aiohttp, json, math, random, sqlite3, time, uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import heapq

# ═══════════════════════════ ENUMS ══════════════════════════════
class NodeStatus(Enum):
    SUCCESS = "SUCCESS"; FAILURE = "FAILURE"; RUNNING = "RUNNING"

class NPCState(Enum):
    IDLE="idle"; PATROL="patrol"; CHASE="chase"; ATTACK="attack"
    FLEE="flee"; SEARCH="search"; INVESTIGATE="investigate"
    INTERACT="interact"; GUARD="guard"; DEAD="dead"

class Personality(Enum):
    AGGRESSIVE="aggressive"; DEFENSIVE="defensive"; NEUTRAL="neutral"
    COWARDLY="cowardly"; BRAVE="brave"; CUNNING="cunning"; FRIENDLY="friendly"

# ══════════════════════ PRIMITIVES ══════════════════════════════
@dataclass
class Vec3:
    x: float=0.0; y: float=0.0; z: float=0.0
    def dist(self, o:"Vec3")->float:
        return math.sqrt((self.x-o.x)**2+(self.y-o.y)**2+(self.z-o.z)**2)
    def copy(self): return Vec3(self.x,self.y,self.z)
    def __repr__(self): return f"({self.x:.1f},{self.y:.1f},{self.z:.1f})"

@dataclass
class NPCStats:
    health:float=100; max_health:float=100; attack_power:float=25
    defense:float=10; speed:float=5; vision_range:float=20
    hear_range:float=15; attack_range:float=2.5
    aggression:float=0.5; bravery:float=0.5; intelligence:float=0.5
    xp_reward:int=50

@dataclass
class Blackboard:
    _d: Dict[str,Any] = field(default_factory=dict)
    def set(self,k,v): self._d[k]=v
    def get(self,k,d=None): return self._d.get(k,d)
    def has(self,k): return k in self._d
    def clear(self,k): self._d.pop(k,None)

# ══════════════════ BEHAVIOUR TREE NODES ════════════════════════
class BTNode:
    def __init__(self,name=""):
        self.name=name; self.children:List[BTNode]=[]
    def add(self,*ns:"BTNode")->"BTNode":
        self.children.extend(ns); return self
    def tick(self,npc:"NPC",bb:Blackboard)->NodeStatus:
        raise NotImplementedError

class Sequence(BTNode):
    def tick(self,npc,bb):
        for c in self.children:
            s=c.tick(npc,bb)
            if s!=NodeStatus.SUCCESS: return s
        return NodeStatus.SUCCESS

class Selector(BTNode):
    def tick(self,npc,bb):
        for c in self.children:
            s=c.tick(npc,bb)
            if s!=NodeStatus.FAILURE: return s
        return NodeStatus.FAILURE

class Parallel(BTNode):
    def __init__(self,name="",threshold:int=None):
        super().__init__(name); self.threshold=threshold
    def tick(self,npc,bb):
        ok=sum(1 for c in self.children if c.tick(npc,bb)==NodeStatus.SUCCESS)
        return NodeStatus.SUCCESS if ok>=(self.threshold or len(self.children)) else NodeStatus.RUNNING

class Inverter(BTNode):
    def tick(self,npc,bb):
        if not self.children: return NodeStatus.FAILURE
        s=self.children[0].tick(npc,bb)
        return NodeStatus.FAILURE if s==NodeStatus.SUCCESS else \
               NodeStatus.SUCCESS if s==NodeStatus.FAILURE else NodeStatus.RUNNING

class Cooldown(BTNode):
    def __init__(self,name="",secs:float=1.0):
        super().__init__(name); self.secs=secs; self._last=0.0
    def tick(self,npc,bb):
        if time.time()-self._last<self.secs: return NodeStatus.FAILURE
        if not self.children: return NodeStatus.FAILURE
        s=self.children[0].tick(npc,bb)
        if s==NodeStatus.SUCCESS: self._last=time.time()
        return s

class Condition(BTNode):
    def __init__(self,name,fn:Callable[["NPC",Blackboard],bool]):
        super().__init__(name); self.fn=fn
    def tick(self,npc,bb):
        return NodeStatus.SUCCESS if self.fn(npc,bb) else NodeStatus.FAILURE

# ──────────── Condition leaves ────────────
class EnemyVisible(BTNode):
    def tick(self,npc,bb):
        t=npc._nearest_enemy()
        if t and npc.can_see(t):
            bb.set("enemy",t); bb.set("last_enemy_pos",t.pos.copy())
            return NodeStatus.SUCCESS
        return NodeStatus.FAILURE

class InAttackRange(BTNode):
    def tick(self,npc,bb):
        e=bb.get("enemy")
        return NodeStatus.SUCCESS if e and npc.pos.dist(e.pos)<=npc.stats.attack_range else NodeStatus.FAILURE

class HealthBelow(BTNode):
    def __init__(self,name="",pct:float=0.25): super().__init__(name); self.pct=pct
    def tick(self,npc,bb):
        return NodeStatus.SUCCESS if npc.stats.health/npc.stats.max_health<=self.pct else NodeStatus.FAILURE

class HasPatrol(BTNode):
    def tick(self,npc,bb): return NodeStatus.SUCCESS if npc.patrol_pts else NodeStatus.FAILURE

class IsAlerted(BTNode):
    def tick(self,npc,bb): return NodeStatus.SUCCESS if bb.get("alerted") else NodeStatus.FAILURE

# ──────────── Action leaves ────────────
class MoveToEnemy(BTNode):
    def tick(self,npc,bb):
        e=bb.get("enemy")
        if not e: return NodeStatus.FAILURE
        if npc.pos.dist(e.pos)<=npc.stats.attack_range: return NodeStatus.SUCCESS
        npc._move_toward(e.pos); npc.state=NPCState.CHASE; return NodeStatus.RUNNING

class AttackEnemy(BTNode):
    def tick(self,npc,bb):
        e=bb.get("enemy")
        if not e: return NodeStatus.FAILURE
        npc._do_attack(e); return NodeStatus.SUCCESS

class FleeFromEnemy(BTNode):
    def tick(self,npc,bb):
        e=bb.get("enemy")
        if not e: return NodeStatus.FAILURE
        npc._flee_from(e.pos); npc.state=NPCState.FLEE; return NodeStatus.RUNNING

class DoPatrol(BTNode):
    def tick(self,npc,bb): npc._patrol_step(); return NodeStatus.RUNNING

class SearchLastPos(BTNode):
    def tick(self,npc,bb):
        lp=bb.get("last_enemy_pos")
        if not lp: return NodeStatus.FAILURE
        npc._move_toward(lp,0.7); npc.state=NPCState.SEARCH
        if npc.pos.dist(lp)<1.5:
            bb.clear("last_enemy_pos"); bb.clear("alerted"); return NodeStatus.SUCCESS
        return NodeStatus.RUNNING

class AlertAllies(BTNode):
    def tick(self,npc,bb):
        npc._alert_allies(bb.get("enemy")); bb.set("alerted",True); return NodeStatus.SUCCESS

class TakeCover(BTNode):
    def tick(self,npc,bb):
        c=npc._find_cover()
        if c: npc._move_toward(c); npc.state=NPCState.FLEE; return NodeStatus.RUNNING
        return NodeStatus.FAILURE

class IdleAction(BTNode):
    def tick(self,npc,bb): npc.state=NPCState.IDLE; return NodeStatus.SUCCESS

# ═══════════════════════════ NPC ════════════════════════════════
class NPC:
    def __init__(self,npc_id:str,name:str,pos:Vec3,
                 personality:Personality=Personality.NEUTRAL,
                 stats:NPCStats=None,npc_type:str="generic"):
        self.npc_id=npc_id; self.name=name; self.pos=pos
        self.personality=personality; self.stats=stats or NPCStats()
        self.npc_type=npc_type; self.state=NPCState.IDLE
        self.patrol_pts:List[Vec3]=[]; self._pi=0
        self.allies:List[NPC]=[]; self.enemies:List[NPC]=[]
        self.memory:List[Dict]=[]
        self.bb=Blackboard(); self.bt:Optional[BTNode]=None
        self._build_tree()

    def _build_tree(self):
        root=Selector("root")
        # dead
        dead=Sequence("dead")
        dead.add(Condition("isDead",lambda n,b:n.stats.health<=0))
        root.add(dead)
        # combat
        combat=Sequence("combat")
        combat.add(EnemyVisible(),AlertAllies())
        inner=Selector("inner")
        if self.personality==Personality.COWARDLY:
            inner.add(FleeFromEnemy())
        else:
            if self.personality!=Personality.BRAVE:
                flee_s=Sequence("flee_s"); flee_s.add(HealthBelow("hp",0.2),FleeFromEnemy()); inner.add(flee_s)
            if self.personality==Personality.CUNNING: inner.add(TakeCover())
            atk=Sequence("atk"); atk.add(InAttackRange(),Cooldown("cd",1.2).add(AttackEnemy()))
            inner.add(atk,MoveToEnemy())
        combat.add(inner); root.add(combat)
        # search
        srch=Sequence("srch"); srch.add(IsAlerted(),SearchLastPos()); root.add(srch)
        # patrol
        pat=Sequence("pat"); pat.add(HasPatrol(),DoPatrol()); root.add(pat)
        root.add(IdleAction()); self.bt=root

    def tick(self):
        if self.bt: self.bt.tick(self,self.bb)

    def can_see(self,o:"NPC")->bool:
        return o.stats.health>0 and self.pos.dist(o.pos)<=self.stats.vision_range

    def _nearest_enemy(self)->Optional["NPC"]:
        alive=[e for e in self.enemies if e.stats.health>0]
        return min(alive,key=lambda e:self.pos.dist(e.pos),default=None)

    def _move_toward(self,t:Vec3,mult:float=1.0):
        dx,dz=t.x-self.pos.x,t.z-self.pos.z
        d=math.sqrt(dx*dx+dz*dz)
        if d>0.05:
            s=self.stats.speed*mult*0.016
            self.pos.x+=dx/d*s; self.pos.z+=dz/d*s

    def _flee_from(self,t:Vec3):
        dx,dz=self.pos.x-t.x,self.pos.z-t.z
        d=math.sqrt(dx*dx+dz*dz)
        if d>0.05:
            s=self.stats.speed*1.3*0.016
            self.pos.x+=dx/d*s; self.pos.z+=dz/d*s

    def _patrol_step(self):
        if not self.patrol_pts: return
        t=self.patrol_pts[self._pi]
        if self.pos.dist(t)<1.0: self._pi=(self._pi+1)%len(self.patrol_pts)
        else: self._move_toward(t,0.6)
        self.state=NPCState.PATROL

    def _do_attack(self,target:"NPC"):
        raw=self.stats.attack_power*random.uniform(0.85,1.15)
        dmg=max(1.0,raw-target.stats.defense*0.4)
        target.receive_damage(dmg,self)
        self.memory.append({"event":"attack","target":target.npc_id,"dmg":round(dmg,1),"t":time.time()})

    def receive_damage(self,amount:float,attacker:"NPC"=None):
        self.stats.health=max(0.0,self.stats.health-amount)
        if attacker:
            if attacker not in self.enemies: self.enemies.append(attacker)
            self.bb.set("enemy",attacker)
            self.bb.set("last_enemy_pos",attacker.pos.copy())
            self.bb.set("alerted",True)

    def _alert_allies(self,enemy:Optional["NPC"]=None):
        for a in self.allies:
            if self.pos.dist(a.pos)<=self.stats.hear_range*2:
                a.bb.set("alerted",True)
                if enemy and enemy not in a.enemies: a.enemies.append(enemy)

    def _find_cover(self)->Vec3:
        return Vec3(self.pos.x+random.uniform(-8,8),self.pos.y,self.pos.z+random.uniform(-8,8))

    def to_dict(self)->Dict:
        return {"npc_id":self.npc_id,"name":self.name,"type":self.npc_type,
                "state":self.state.value,"personality":self.personality.value,
                "pos":{"x":self.pos.x,"y":self.pos.y,"z":self.pos.z},
                "hp":round(self.stats.health,1),"max_hp":self.stats.max_health}

# ═══════════════════════ A* PATHFINDER ══════════════════════════
class AStarPathfinder:
    def __init__(self,w:int=100,h:int=100):
        self.w=w; self.h=h; self.obstacles:set=set()
    def block(self,x:int,z:int): self.obstacles.add((x,z))
    def find_path(self,start:Vec3,end:Vec3)->List[Vec3]:
        sx,sz,ex,ez=int(start.x),int(start.z),int(end.x),int(end.z)
        @dataclass(order=True)
        class Node:
            f:float; pos:Tuple[int,int]=field(compare=False)
            g:float=field(compare=False,default=0.0); parent:Any=field(compare=False,default=None)
        heap=[]; closed=set()
        heapq.heappush(heap,Node(0,(sx,sz)))
        while heap:
            cur=heapq.heappop(heap); cx,cz=cur.pos
            if (cx,cz)==(ex,ez):
                path=[]; n=cur
                while n: path.append(Vec3(n.pos[0],0,n.pos[1])); n=n.parent
                return list(reversed(path))
            closed.add((cx,cz))
            for dx,dz in [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]:
                nx,nz=cx+dx,cz+dz
                if (nx,nz) in closed or (nx,nz) in self.obstacles: continue
                if not(0<=nx<self.w and 0<=nz<self.h): continue
                g=cur.g+(1.414 if dx and dz else 1.0)
                heapq.heappush(heap,Node(g+abs(nx-ex)+abs(nz-ez),(nx,nz),g,cur))
        return []

# ═══════════════════════ FSM ════════════════════════════════════
class FSMState:
    def __init__(self,name:str,on_enter=None,on_tick=None,on_exit=None):
        self.name=name; self.on_enter=on_enter; self.on_tick=on_tick; self.on_exit=on_exit
        self.trans:Dict[str,str]={}
    def via(self,trigger:str,to:str)->"FSMState": self.trans[trigger]=to; return self

class FSM:
    def __init__(self,initial:str): self.states:Dict[str,FSMState]={}; self.current=initial; self.prev=initial
    def add(self,*ss:"FSMState")->"FSM":
        for s in ss: self.states[s.name]=s; return self
    def trigger(self,ev:str)->bool:
        s=self.states.get(self.current)
        if s and ev in s.trans:
            if s.on_exit: s.on_exit()
            self.prev=self.current; self.current=s.trans[ev]
            ns=self.states.get(self.current)
            if ns and ns.on_enter: ns.on_enter(); return True
        return False
    def tick(self,npc:NPC):
        s=self.states.get(self.current)
        if s and s.on_tick: s.on_tick(npc)

def make_guard_fsm()->FSM:
    return FSM("patrol").add(
        FSMState("patrol").via("spot","chase").via("noise","investigate"),
        FSMState("investigate").via("spot","chase").via("timeout","patrol"),
        FSMState("chase").via("in_range","attack").via("lost","search"),
        FSMState("attack").via("out","chase").via("low_hp","flee").via("killed","patrol"),
        FSMState("search").via("found","chase").via("timeout","patrol"),
        FSMState("flee").via("safe","patrol"),
        FSMState("dead"),
    )

# ═══════════════════════ GOAP ═══════════════════════════════════
@dataclass
class GOAPAction:
    name:str; preconditions:Dict[str,Any]; effects:Dict[str,Any]; cost:float=1.0
    def applicable(self,state:Dict)->bool: return all(state.get(k)==v for k,v in self.preconditions.items())
    def apply(self,state:Dict)->Dict: return {**state,**self.effects}

class GOAPPlanner:
    def plan(self,start:Dict,goal:Dict,actions:List[GOAPAction],depth:int=10)->List[GOAPAction]:
        best=[]; best_cost=[float("inf")]
        def _s(state,needed,path,cost):
            if not needed:
                if cost<best_cost[0]: best_cost[0]=cost; best.clear(); best.extend(path); return
            if len(path)>=depth: return
            for a in actions:
                if not a.applicable(state): continue
                ns=a.apply(state)
                still={k:v for k,v in needed.items() if ns.get(k)!=v}
                _s(ns,still,path+[a],cost+a.cost)
        _s(start,dict(goal),[],0); return best

def default_goap_actions()->List[GOAPAction]:
    return [
        GOAPAction("MoveToEnemy",{"has_weapon":True,"in_range":False},{"in_range":True},1.0),
        GOAPAction("AttackEnemy",{"in_range":True,"enemy_alive":True},{"enemy_alive":False},1.0),
        GOAPAction("Reload",{"ammo":0},{"ammo":30},2.0),
        GOAPAction("Flee",{"health_low":True},{"is_safe":True},0.5),
        GOAPAction("HealSelf",{"has_potion":True,"health_low":True},{"health_low":False},1.5),
        GOAPAction("TakeCover",{"under_fire":True},{"in_cover":True},1.0),
        GOAPAction("AlertAllies",{"enemy_alive":True,"allies_alerted":False},{"allies_alerted":True},0.5),
        GOAPAction("UseAbility",{"ability_ready":True,"in_range":True},{"enemy_alive":False},0.8),
    ]

# ════════════════════════ NPC MANAGER ═══════════════════════════
class NPCManager:
    TEMPLATES:Dict[str,Dict]={
        "guard":    {"p":Personality.NEUTRAL,   "s":NPCStats(health=120,attack_power=20,defense=15,speed=4.5,vision_range=18)},
        "warrior":  {"p":Personality.AGGRESSIVE,"s":NPCStats(health=150,attack_power=35,defense=20,speed=5.0,aggression=0.9)},
        "archer":   {"p":Personality.DEFENSIVE,  "s":NPCStats(health=80, attack_power=30,defense=5, speed=4.0,vision_range=30,attack_range=15)},
        "mage":     {"p":Personality.CUNNING,    "s":NPCStats(health=70, attack_power=50,defense=5, speed=3.5,attack_range=12,intelligence=0.9)},
        "coward":   {"p":Personality.COWARDLY,   "s":NPCStats(health=60, attack_power=10,defense=5, speed=6.0,bravery=0.1)},
        "boss":     {"p":Personality.AGGRESSIVE,  "s":NPCStats(health=500,attack_power=60,defense=30,speed=4.0,bravery=1.0,intelligence=0.8,xp_reward=500)},
        "merchant": {"p":Personality.FRIENDLY,   "s":NPCStats(health=80, attack_power=5, defense=5, speed=3.0,aggression=0.0)},
        "villager": {"p":Personality.COWARDLY,   "s":NPCStats(health=50, attack_power=3, defense=2, speed=3.5,aggression=0.0,bravery=0.1)},
    }

    def __init__(self,openai_key:str=""):
        self.openai_key=openai_key; self.npcs:Dict[str,NPC]={}
        self.pathfinder=AStarPathfinder(); self.goap=GOAPPlanner()
        self._init_db()

    def _init_db(self):
        c=sqlite3.connect("behavior_system.db")
        c.executescript("""
        CREATE TABLE IF NOT EXISTS npc_templates(id TEXT PRIMARY KEY,name TEXT,personality TEXT,stats TEXT,created_at TEXT);
        CREATE TABLE IF NOT EXISTS combat_log(id INTEGER PRIMARY KEY AUTOINCREMENT,attacker TEXT,defender TEXT,damage REAL,ts TEXT);
        CREATE TABLE IF NOT EXISTS behavior_events(id INTEGER PRIMARY KEY AUTOINCREMENT,npc_id TEXT,event TEXT,data TEXT,ts TEXT);
        """); c.commit(); c.close()

    def spawn(self,npc_type:str,name:str,pos:Vec3,npc_id:str=None,patrol:List[Vec3]=None,**overrides)->NPC:
        t=self.TEMPLATES.get(npc_type,self.TEMPLATES["guard"])
        base=t["s"].__dict__.copy(); base.update(overrides)
        npc=NPC(npc_id or str(uuid.uuid4())[:8],name,pos,t["p"],NPCStats(**base),npc_type)
        if patrol: npc.patrol_pts=patrol
        self.npcs[npc.npc_id]=npc; return npc

    def form_group(self,*ids:str):
        for i in ids:
            if i in self.npcs:
                self.npcs[i].allies=[self.npcs[j] for j in ids if j!=i and j in self.npcs]

    def add_enemies(self,a_ids:List[str],b_ids:List[str]):
        for ai in a_ids:
            for bi in b_ids:
                a,b=self.npcs.get(ai),self.npcs.get(bi)
                if a and b:
                    if b not in a.enemies: a.enemies.append(b)
                    if a not in b.enemies: b.enemies.append(a)

    def tick_all(self):
        for n in list(self.npcs.values()):
            if n.stats.health>0: n.tick()

    def simulate(self,ticks:int=60):
        for _ in range(ticks): self.tick_all()

    async def generate_from_description(self,description:str)->Dict:
        prompt=f"""Design a game NPC: {description}
Return ONLY JSON:
{{"name":"str","type":"guard|warrior|archer|mage|boss|merchant|villager",
"personality":"aggressive|defensive|neutral|cowardly|brave|cunning|friendly",
"health":100,"attack_power":25,"defense":10,"speed":5.0,"vision_range":20.0,
"behavior_notes":"str","patrol_radius":10}}"""
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post("https://api.openai.com/v1/chat/completions",
                    headers={"Authorization":f"Bearer {self.openai_key}","Content-Type":"application/json"},
                    json={"model":"gpt-4-turbo-preview","messages":[{"role":"user","content":prompt}],
                          "response_format":{"type":"json_object"}}) as r:
                    d=await r.json()
                    return json.loads(d["choices"][0]["message"]["content"])
        except: return {"name":"NPC","type":"guard","personality":"neutral","health":100}

    def export_unreal(self,out:str="exports")->str:
        Path(out).mkdir(parents=True,exist_ok=True)
        p=f"{out}/npc_config_{int(time.time())}.json"
        Path(p).write_text(json.dumps({"schema":"1.0","generated":datetime.utcnow().isoformat(),
            "npcs":[n.to_dict() for n in self.npcs.values()]},indent=2)); return p

    def world_state(self)->Dict:
        return {"total":len(self.npcs),
                "alive":sum(1 for n in self.npcs.values() if n.stats.health>0),
                "by_state":{s.value:sum(1 for n in self.npcs.values() if n.state==s) for s in NPCState},
                "npcs":[n.to_dict() for n in self.npcs.values()]}

# ════════════════════════ QUICK DEMO ════════════════════════════
if __name__=="__main__":
    mgr=NPCManager()
    patrol=[Vec3(0,0,0),Vec3(10,0,0),Vec3(10,0,10),Vec3(0,0,10)]
    g=mgr.spawn("guard",  "Guard",  Vec3(0,0,0),  patrol=patrol)
    a=mgr.spawn("archer", "Archer", Vec3(5,0,5))
    p=mgr.spawn("warrior","Player", Vec3(25,0,25))
    mgr.form_group(g.npc_id,a.npc_id)
    mgr.add_enemies([g.npc_id,a.npc_id],[p.npc_id])
    mgr.simulate(30)
    print(json.dumps(mgr.world_state(),indent=2))
    plan=GOAPPlanner().plan(
        {"has_weapon":True,"in_range":False,"enemy_alive":True,"ammo":10,"health_low":False,"under_fire":False,"allies_alerted":False},
        {"enemy_alive":False},default_goap_actions())
    print("GOAP plan:",[x.name for x in plan])
    