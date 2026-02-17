# Jinja2 Template System for Code Generation

## UCLASS Boilerplate Template
```cpp
// {{ class_name }}.h
#pragma once

#include "CoreMinimal.h"
#include "{{ base_class_include }}"
#include "{{ class_name }}.generated.h"

{% if forward_declarations %}
// Forward declarations
{% for decl in forward_declarations %}
class {{ decl }};
{% endfor %}
{% endif %}

/**
 * {{ description }}
 */
UCLASS({{ uclass_specifiers }})
class {{ api_macro }} {{ class_name }} : public {{ base_class }}
{
    GENERATED_BODY()

public:
    // Constructor
    {{ class_name }}();

protected:
    // Called when the game starts or when spawned
    virtual void BeginPlay() override;

public:
    // Called every frame
    virtual void Tick(float DeltaTime) override;

    {% if properties %}
    // Properties
    {% for prop in properties %}
    UPROPERTY({{ prop.specifiers }})
    {{ prop.type }} {{ prop.name }};
    {% endfor %}
    {% endif %}

    {% if functions %}
    // Functions
    {% for func in functions %}
    UFUNCTION({{ func.specifiers }})
    {{ func.return_type }} {{ func.name }}({{ func.params }});
    {% endfor %}
    {% endif %}

private:
    {% if private_members %}
    {% for member in private_members %}
    {{ member.type }} {{ member.name }};
    {% endfor %}
    {% endif %}
};
```

```cpp
// {{ class_name }}.cpp
#include "{{ class_name }}.h"

{{ class_name }}::{{ class_name }}()
{
    // Set this actor to call Tick() every frame
    PrimaryActorTick.bCanEverTick = {{ can_tick }};

    {% if component_initializations %}
    // Initialize components
    {% for init in component_initializations %}
    {{ init }}
    {% endfor %}
    {% endif %}

    UE_LOG(LogTemp, Log, TEXT("{{ class_name }} constructed"));
}

void {{ class_name }}::BeginPlay()
{
    Super::BeginPlay();
    
    UE_LOG(LogTemp, Log, TEXT("{{ class_name }} BeginPlay"));
    
    {% if begin_play_logic %}
    {{ begin_play_logic }}
    {% endif %}
}

void {{ class_name }}::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);

    {% if tick_logic %}
    {{ tick_logic }}
    {% endif %}
}

{% if function_implementations %}
{% for impl in function_implementations %}
{{ impl }}
{% endfor %}
{% endif %}
```

## Build.cs Template
```csharp
// {{ module_name }}.Build.cs
using UnrealBuildTool;

public class {{ module_name }} : ModuleRules
{
    public {{ module_name }}(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[] 
        { 
            {% for dep in public_dependencies %}
            "{{ dep }}"{{ "," if not loop.last else "" }}
            {% endfor %}
        });

        PrivateDependencyModuleNames.AddRange(new string[] 
        { 
            {% for dep in private_dependencies %}
            "{{ dep }}"{{ "," if not loop.last else "" }}
            {% endfor %}
        });

        {% if include_paths %}
        PublicIncludePaths.AddRange(new string[] 
        {
            {% for path in include_paths %}
            "{{ path }}"{{ "," if not loop.last else "" }}
            {% endfor %}
        });
        {% endif %}

        {% if definitions %}
        PublicDefinitions.AddRange(new string[]
        {
            {% for def in definitions %}
            "{{ def }}"{{ "," if not loop.last else "" }}
            {% endfor %}
        });
        {% endif %}

        {% if platform_specific %}
        if (Target.Platform == UnrealTargetPlatform.Win64)
        {
            {{ platform_specific.win64 }}
        }
        else if (Target.Platform == UnrealTargetPlatform.Linux)
        {
            {{ platform_specific.linux }}
        }
        {% endif %}
    }
}
```

## Plugin Structure Template (.uplugin)
```json
{
    "FileVersion": 3,
    "Version": {{ version }},
    "VersionName": "{{ version_name }}",
    "FriendlyName": "{{ friendly_name }}",
    "Description": "{{ description }}",
    "Category": "{{ category }}",
    "CreatedBy": "{{ created_by }}",
    "CreatedByURL": "{{ created_by_url }}",
    "DocsURL": "{{ docs_url }}",
    "MarketplaceURL": "{{ marketplace_url }}",
    "SupportURL": "{{ support_url }}",
    "CanContainContent": {{ can_contain_content|lower }},
    "IsBetaVersion": {{ is_beta|lower }},
    "IsExperimentalVersion": {{ is_experimental|lower }},
    "Installed": false,
    "Modules": [
        {% for module in modules %}
        {
            "Name": "{{ module.name }}",
            "Type": "{{ module.type }}",
            "LoadingPhase": "{{ module.loading_phase }}"
        }{{ "," if not loop.last else "" }}
        {% endfor %}
    ]
    {% if plugins %}
    ,
    "Plugins": [
        {% for plugin in plugins %}
        {
            "Name": "{{ plugin.name }}",
            "Enabled": {{ plugin.enabled|lower }}
        }{{ "," if not loop.last else "" }}
        {% endfor %}
    ]
    {% endif %}
}
```

## CMakeLists Template
```cmake
cmake_minimum_required(VERSION {{ cmake_version }})
project({{ project_name }} VERSION {{ version }})

set(CMAKE_CXX_STANDARD {{ cxx_standard }})
set(CMAKE_CXX_STANDARD_REQUIRED ON)

{% if options %}
# Options
{% for option in options %}
option({{ option.name }} "{{ option.description }}" {{ option.default }})
{% endfor %}
{% endif %}

{% if dependencies %}
# Find dependencies
{% for dep in dependencies %}
find_package({{ dep.name }} {{ dep.version }} REQUIRED)
{% endfor %}
{% endif %}

# Include directories
include_directories(
    {% for inc in include_directories %}
    {{ inc }}
    {% endfor %}
)

# Source files
set(SOURCES
    {% for src in sources %}
    {{ src }}
    {% endfor %}
)

set(HEADERS
    {% for hdr in headers %}
    {{ hdr }}
    {% endfor %}
)

{% if library_type == "SHARED" %}
add_library(${PROJECT_NAME} SHARED ${SOURCES} ${HEADERS})
{% elif library_type == "STATIC" %}
add_library(${PROJECT_NAME} STATIC ${SOURCES} ${HEADERS})
{% else %}
add_executable(${PROJECT_NAME} ${SOURCES} ${HEADERS})
{% endif %}

{% if link_libraries %}
# Link libraries
target_link_libraries(${PROJECT_NAME}
    {% for lib in link_libraries %}
    {{ lib }}
    {% endfor %}
)
{% endif %}

{% if compile_definitions %}
# Compile definitions
target_compile_definitions(${PROJECT_NAME} PRIVATE
    {% for def in compile_definitions %}
    {{ def }}
    {% endfor %}
)
{% endif %}

{% if install_targets %}
# Install targets
install(TARGETS ${PROJECT_NAME}
    LIBRARY DESTINATION {{ install_lib_dir }}
    ARCHIVE DESTINATION {{ install_lib_dir }}
    RUNTIME DESTINATION {{ install_bin_dir }}
)
{% endif %}
```

## Blender Plugin Template
```python
# __init__.py
bl_info = {
    "name": "{{ addon_name }}",
    "author": "{{ author }}",
    "version": ({{ version.major }}, {{ version.minor }}, {{ version.patch }}),
    "blender": ({{ blender_version.major }}, {{ blender_version.minor }}, 0),
    "location": "{{ location }}",
    "description": "{{ description }}",
    "warning": "{{ warning }}",
    "doc_url": "{{ doc_url }}",
    "category": "{{ category }}",
}

import bpy
{% if imports %}
{% for imp in imports %}
from . import {{ imp }}
{% endfor %}
{% endif %}

{% if classes %}
classes = (
    {% for cls in classes %}
    {{ cls }},
    {% endfor %}
)
{% endif %}

def register():
    {% if classes %}
    for cls in classes:
        bpy.utils.register_class(cls)
    {% endif %}
    
    {% if properties %}
    # Properties
    {% for prop in properties %}
    {{ prop }}
    {% endfor %}
    {% endif %}
    
    print("{{ addon_name }} registered")

def unregister():
    {% if classes %}
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    {% endif %}
    
    {% if properties %}
    # Remove properties
    {% for prop in properties %}
    del {{ prop.target }}
    {% endfor %}
    {% endif %}
    
    print("{{ addon_name }} unregistered")

if __name__ == "__main__":
    register()
```

```python
# operators.py
import bpy

{% for operator in operators %}
class {{ operator.class_name }}(bpy.types.Operator):
    bl_idname = "{{ operator.bl_idname }}"
    bl_label = "{{ operator.bl_label }}"
    bl_description = "{{ operator.description }}"
    bl_options = {{ operator.options }}

    {% if operator.properties %}
    # Properties
    {% for prop in operator.properties %}
    {{ prop.name }}: bpy.props.{{ prop.type }}(
        name="{{ prop.display_name }}",
        description="{{ prop.description }}",
        default={{ prop.default }}
    )
    {% endfor %}
    {% endif %}

    def execute(self, context):
        {{ operator.execute_code | indent(8) }}
        return {'FINISHED'}

    {% if operator.invoke %}
    def invoke(self, context, event):
        {{ operator.invoke_code | indent(8) }}
        return {'RUNNING_MODAL'}
    {% endif %}

{% endfor %}
```

```python
# panels.py
import bpy

{% for panel in panels %}
class {{ panel.class_name }}(bpy.types.Panel):
    bl_label = "{{ panel.bl_label }}"
    bl_idname = "{{ panel.bl_idname }}"
    bl_space_type = '{{ panel.space_type }}'
    bl_region_type = '{{ panel.region_type }}'
    bl_category = "{{ panel.category }}"

    def draw(self, context):
        layout = self.layout
        {{ panel.draw_code | indent(8) }}

{% endfor %}
```