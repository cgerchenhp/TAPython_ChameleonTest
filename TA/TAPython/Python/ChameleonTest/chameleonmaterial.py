import os
import re
import unreal
from Utilities.Utils import Singleton
import Utilities
import json


class ChameleonMaterial(metaclass=Singleton):
    def __init__(self, jsonPath:str):
        self.jsonPath = jsonPath
        self.init_re()

    def init_re(self):
        self.linearColor_re = re.compile(r"\(R=([-\d.]+),G=([-\d.]+),B=([-\d.]+),A=([-\d.]+)\)")
        self.vector4_re = re.compile(r"\(X=([-\d.]+),Y=([-\d.]+),Z=([-\d.]+),W=([-\d.]+)\)")
        self.vector3_re = re.compile(r"\(X=([-\d.]+),Y=([-\d.]+),Z=([-\d.]+)\)")
        self.vector2_re = re.compile(r"\(X=([-\d.]+),Y=([-\d.]+)\)")
        self.lightmess_settings_re = re.compile(r"\(EmissiveBoost=([-\d.]+),DiffuseBoost=([-\d.]+),B=([-\d.]+),ExportResolutionScale=([-\d.]+)\)")

    def on_button_CreateMaterial_click(self):
        print("On Button Create call")
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        my_mat = asset_tools.create_asset("M_CreatedByPython", "/Game/CreatedByPython", unreal.Material,
                                             unreal.MaterialFactoryNew())
        # 1. create
        unreal.EditorAssetLibrary.save_asset(my_mat.get_path_name())

        # 2. add some nodes
        add_node = unreal.MaterialEditingLibrary.create_material_expression(my_mat, unreal.MaterialExpressionAdd)
        unreal.MaterialEditingLibrary.connect_material_property(from_expression=add_node
                                                                , from_output_name=""
                                                                , property_=unreal.MaterialProperty.MP_BASE_COLOR)

        tex_node = unreal.MaterialEditingLibrary.create_material_expression(my_mat, unreal.MaterialExpressionTextureSampleParameter2D)
        unreal.MaterialEditingLibrary.connect_material_expressions(from_expression=tex_node, from_output_name="", to_expression=add_node, to_input_name="A")

        texture_asset = unreal.load_asset("/Game/ImportPools/T_ps_0ff00000000000_6e71a4e7910ee9c92b66da3cc_927b04ac369bce56_1024x1024_BC")
        tex_node.set_editor_property("texture", texture_asset)
        #

        multi_node = unreal.MaterialEditingLibrary.create_material_expression(my_mat, unreal.MaterialExpressionMultiply)
        unreal.MaterialEditingLibrary.connect_material_expressions(multi_node, "", add_node, "B")

        saturate_node = unreal.MaterialEditingLibrary.create_material_expression(my_mat, unreal.MaterialExpressionSaturate)
        unreal.MaterialEditingLibrary.connect_material_expressions(saturate_node, "", multi_node, "A")

        scalar_B = unreal.MaterialEditingLibrary.create_material_expression(my_mat, unreal.MaterialExpressionScalarParameter)
        scalar_B.set_editor_property("default_value", 1)
        scalar_B.set_editor_property("parameter_name", "B")
        unreal.MaterialEditingLibrary.connect_material_expressions(scalar_B, "", multi_node, "B")

        mf_remap = unreal.load_asset("/Engine/Functions/Engine_MaterialFunctions03/Math/RemapValueRange")
        remap_node = unreal.MaterialEditingLibrary.create_material_expression(my_mat, unreal.MaterialExpressionMaterialFunctionCall)
        remap_node.set_editor_property("material_function", mf_remap)
        unreal.MaterialEditingLibrary.connect_material_expressions(remap_node, "Result", saturate_node, "")

        abs_node = unreal.MaterialEditingLibrary.create_material_expression(my_mat, unreal.MaterialExpressionAbs)
        unreal.MaterialEditingLibrary.connect_material_expressions(abs_node, "", remap_node, "Input")
        # remap
        for i, (input_name, default_value) in enumerate(zip(["Input Low", "Input High", "Target Low", "Target High"]
                                                            , [0.4, 0.5, 0, 1])):
            n = unreal.MaterialEditingLibrary.create_material_expression(my_mat, unreal.MaterialExpressionConstant)
            n.set_editor_property("r", default_value)
            unreal.MaterialEditingLibrary.connect_material_expressions(n, "", remap_node, input_name)

        sub_node = unreal.MaterialEditingLibrary.create_material_expression(my_mat, unreal.MaterialExpressionSubtract)
        sub_node.set_editor_property("const_b", 0.5)
        unreal.MaterialEditingLibrary.connect_material_expressions(sub_node, "", abs_node, "")

        fmod_node = unreal.MaterialEditingLibrary.create_material_expression(my_mat, unreal.MaterialExpressionFmod)
        unreal.MaterialEditingLibrary.connect_material_expressions(fmod_node, "", sub_node, "")

        multi_node_b = unreal.MaterialEditingLibrary.create_material_expression(my_mat, unreal.MaterialExpressionMultiply)
        unreal.MaterialEditingLibrary.connect_material_expressions(multi_node_b, "", fmod_node, "A")
        multi_node_b.set_editor_property("const_b", 5)

        one_node = unreal.MaterialEditingLibrary.create_material_expression(my_mat, unreal.MaterialExpressionConstant)
        one_node.set_editor_property("r", 1)
        unreal.MaterialEditingLibrary.connect_material_expressions(one_node, "", fmod_node, "B")

        break_node = unreal.MaterialEditingLibrary.create_material_expression(my_mat, unreal.MaterialExpressionMaterialFunctionCall)
        break_node.set_editor_property("material_function", unreal.load_asset("/Engine/Functions/Engine_MaterialFunctions02/Utility/BreakOutFloat2Components"))
        unreal.MaterialEditingLibrary.connect_material_expressions(break_node, "", multi_node_b, "A")

        panner_node = unreal.MaterialEditingLibrary.create_material_expression(my_mat, unreal.MaterialExpressionPanner)
        unreal.MaterialEditingLibrary.connect_material_expressions(panner_node, "", break_node, "")

        coord_node = unreal.MaterialEditingLibrary.create_material_expression(my_mat, unreal.MaterialExpressionTextureCoordinate)
        unreal.MaterialEditingLibrary.connect_material_expressions(coord_node, "", panner_node, "Coordinate")

        time_node = unreal.MaterialEditingLibrary.create_material_expression(my_mat, unreal.MaterialExpressionTime)
        unreal.MaterialEditingLibrary.connect_material_expressions(time_node, "", panner_node, "time")

        make_node = unreal.MaterialEditingLibrary.create_material_expression(my_mat, unreal.MaterialExpressionMaterialFunctionCall)
        make_node.set_editor_property("material_function", unreal.load_asset('/Engine/Functions/Engine_MaterialFunctions02/Utility/MakeFloat2.MakeFloat2'))
        unreal.MaterialEditingLibrary.connect_material_expressions(make_node, "", panner_node, "Speed")

        speed_node = unreal.MaterialEditingLibrary.create_material_expression(my_mat, unreal.MaterialExpressionVectorParameter)
        speed_node.set_editor_property("default_value", unreal.LinearColor(0.1, 0, 0, 1))
        unreal.MaterialEditingLibrary.connect_material_expressions(speed_node, "r", make_node, "x")
        unreal.MaterialEditingLibrary.connect_material_expressions(speed_node, "g", make_node, "y")

        unreal.MaterialEditingLibrary.layout_material_expressions(my_mat)
        unreal.EditorAssetLibrary.save_asset(my_mat.get_path_name())

    def on_button_CreateMF_click(self):
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        my_mf = asset_tools.create_asset("MF_CreatedByPython", "/Game/CreatedByPython", unreal.MaterialFunction,
                                          unreal.MaterialFunctionFactoryNew())
        # 1. create
        unreal.EditorAssetLibrary.save_asset(my_mf.get_path_name())
        # 2. output node
        output_node =unreal.MaterialEditingLibrary.create_material_expression_in_function(my_mf, unreal.MaterialExpressionFunctionOutput)


        multi_node = unreal.MaterialEditingLibrary.create_material_expression_in_function(my_mf, unreal.MaterialExpressionMultiply)
        unreal.MaterialEditingLibrary.connect_material_expressions(multi_node, "", output_node, "")

        saturate_node = unreal.MaterialEditingLibrary.create_material_expression_in_function(my_mf,
                                                                                 unreal.MaterialExpressionSaturate)
        unreal.MaterialEditingLibrary.connect_material_expressions(saturate_node, "", multi_node, "A")

        scalar_B = unreal.MaterialEditingLibrary.create_material_expression_in_function(my_mf,
                                                                            unreal.MaterialExpressionScalarParameter)
        scalar_B.set_editor_property("default_value", 1)
        scalar_B.set_editor_property("parameter_name", "B")
        unreal.MaterialEditingLibrary.connect_material_expressions(scalar_B, "", multi_node, "B")

        mf_remap = unreal.load_asset("/Engine/Functions/Engine_MaterialFunctions03/Math/RemapValueRange")
        remap_node = unreal.MaterialEditingLibrary.create_material_expression_in_function(my_mf,
                                                                              unreal.MaterialExpressionMaterialFunctionCall)
        remap_node.set_editor_property("material_function", mf_remap)
        unreal.MaterialEditingLibrary.connect_material_expressions(remap_node, "Result", saturate_node, "")

        abs_node = unreal.MaterialEditingLibrary.create_material_expression_in_function(my_mf, unreal.MaterialExpressionAbs)
        unreal.MaterialEditingLibrary.connect_material_expressions(abs_node, "", remap_node, "Input")
        # remap
        for i, (input_name, default_value) in enumerate(zip(["Input Low", "Input High", "Target Low", "Target High"]
                , [0.4, 0.5, 0, 1])):
            n = unreal.MaterialEditingLibrary.create_material_expression_in_function(my_mf, unreal.MaterialExpressionConstant)
            n.set_editor_property("r", default_value)
            unreal.MaterialEditingLibrary.connect_material_expressions(n, "", remap_node, input_name)

        sub_node = unreal.MaterialEditingLibrary.create_material_expression_in_function(my_mf, unreal.MaterialExpressionSubtract)
        sub_node.set_editor_property("const_b", 0.5)
        unreal.MaterialEditingLibrary.connect_material_expressions(sub_node, "", abs_node, "")

        fmod_node = unreal.MaterialEditingLibrary.create_material_expression_in_function(my_mf, unreal.MaterialExpressionFmod)
        unreal.MaterialEditingLibrary.connect_material_expressions(fmod_node, "", sub_node, "")

        multi_node_b = unreal.MaterialEditingLibrary.create_material_expression_in_function(my_mf,
                                                                                unreal.MaterialExpressionMultiply)
        unreal.MaterialEditingLibrary.connect_material_expressions(multi_node_b, "", fmod_node, "A")
        multi_node_b.set_editor_property("const_b", 5)

        one_node = unreal.MaterialEditingLibrary.create_material_expression_in_function(my_mf, unreal.MaterialExpressionConstant)
        one_node.set_editor_property("r", 1)
        unreal.MaterialEditingLibrary.connect_material_expressions(one_node, "", fmod_node, "B")

        break_node = unreal.MaterialEditingLibrary.create_material_expression_in_function(my_mf,
                                                                              unreal.MaterialExpressionMaterialFunctionCall)
        break_node.set_editor_property("material_function", unreal.load_asset(
            "/Engine/Functions/Engine_MaterialFunctions02/Utility/BreakOutFloat2Components"))
        unreal.MaterialEditingLibrary.connect_material_expressions(break_node, "", multi_node_b, "A")

        panner_node = unreal.MaterialEditingLibrary.create_material_expression_in_function(my_mf, unreal.MaterialExpressionPanner)
        unreal.MaterialEditingLibrary.connect_material_expressions(panner_node, "", break_node, "")

        coord_node = unreal.MaterialEditingLibrary.create_material_expression_in_function(my_mf,
                                                                              unreal.MaterialExpressionTextureCoordinate)
        unreal.MaterialEditingLibrary.connect_material_expressions(coord_node, "", panner_node, "Coordinate")

        time_node = unreal.MaterialEditingLibrary.create_material_expression_in_function(my_mf, unreal.MaterialExpressionTime)
        unreal.MaterialEditingLibrary.connect_material_expressions(time_node, "", panner_node, "time")

        make_node = unreal.MaterialEditingLibrary.create_material_expression_in_function(my_mf,
                                                                             unreal.MaterialExpressionMaterialFunctionCall)
        make_node.set_editor_property("material_function", unreal.load_asset(
            '/Engine/Functions/Engine_MaterialFunctions02/Utility/MakeFloat2.MakeFloat2'))
        unreal.MaterialEditingLibrary.connect_material_expressions(make_node, "", panner_node, "Speed")

        speed_node = unreal.MaterialEditingLibrary.create_material_expression_in_function(my_mf,
                                                                              unreal.MaterialExpressionVectorParameter)
        speed_node.set_editor_property("default_value", unreal.LinearColor(0.1, 0, 0, 1))
        unreal.MaterialEditingLibrary.connect_material_expressions(speed_node, "r", make_node, "x")
        unreal.MaterialEditingLibrary.connect_material_expressions(speed_node, "g", make_node, "y")


        # --
        unreal.MaterialEditingLibrary.layout_material_function_expressions(my_mf)

        unreal.EditorAssetLibrary.save_asset(my_mf.get_path_name())


    def get_created_mat_path(self):
        return "/Game/CreatedByPython/M_CreatedByPython"

    def on_button_CreateMaterialWithMF_click(self):
        print("on_button_CreateMaterialWithMF_click call")
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        my_mat = asset_tools.create_asset("M_WithMF", "/Game/CreatedByPython", unreal.Material, unreal.MaterialFactoryNew())
        # 1. create
        unreal.EditorAssetLibrary.save_asset(my_mat.get_path_name())

        # 2. add some nodes
        add_node = unreal.MaterialEditingLibrary.create_material_expression(my_mat, unreal.MaterialExpressionAdd)
        unreal.MaterialEditingLibrary.connect_material_property(from_expression=add_node
                                                                , from_output_name=""
                                                                , property_=unreal.MaterialProperty.MP_BASE_COLOR)

        tex_node = unreal.MaterialEditingLibrary.create_material_expression(my_mat, unreal.MaterialExpressionTextureSampleParameter2D)
        texture_asset = unreal.load_asset("/Game/ImportPools/T_ps_0ff00000000000_6e71a4e7910ee9c92b66da3cc_927b04ac369bce56_1024x1024_BC")
        tex_node.set_editor_property("texture", texture_asset)

        unreal.MaterialEditingLibrary.connect_material_expressions(from_expression=tex_node, from_output_name=""
                                                                   , to_expression=add_node, to_input_name="A")

        # 3. add the MF
        mf_created_by_python = unreal.load_asset("/Game/CreatedByPython/MF_CreatedByPython")
        mf_node = unreal.MaterialEditingLibrary.create_material_expression(my_mat , unreal.MaterialExpressionMaterialFunctionCall)
        mf_node.set_editor_property("material_function", mf_created_by_python)
        unreal.MaterialEditingLibrary.connect_material_expressions(from_expression=mf_node, from_output_name=""
                                                                   , to_expression=add_node, to_input_name="B")

        unreal.MaterialEditingLibrary.layout_material_expressions(my_mat)
        unreal.MaterialEditingLibrary.recompile_material(my_mat)
        unreal.EditorAssetLibrary.save_asset(my_mat.get_path_name())


    def on_button_Del_click(self):
        unreal.EditorAssetLibrary.delete_asset(self.get_created_mat_path())
        unreal.EditorAssetLibrary.delete_asset("/Game/CreatedByPython/MF_CreatedByPython")
        unreal.EditorAssetLibrary.delete_asset("/Game/CreatedByPython/M_WithMF")

    def on_button_logMatMf_click(self):
        selection = Utilities.Utils.get_selected_assets()
        for sel in selection:
            if isinstance(sel, unreal.Material):
                unreal.PythonMaterialLib.log_mat_tree(sel)
            elif isinstance(sel, unreal.MaterialFunction):
                unreal.PythonMaterialLib.log_mf(sel)

    def on_button_GetMatSource_click(self):
        selection = Utilities.Utils.get_selected_assets()
        if selection:
            source = unreal.PythonMaterialLib.get_material_expression_source(selection[0])
            print(source)

    def trans_enum_str(self, enum_str):
        result = ""
        s0 = enum_str[:enum_str.find("_")+1]
        s1 = enum_str[enum_str.find("_")+1:]
        new_s1 = ""

        for i, c in enumerate(s1):
            if c.isupper() and i > 0 and s1[i-1].isupper():
                c = c.lower()
            new_s1 += c
        enum_str = s0 + new_s1
        bV = False
        for i, c in enumerate(enum_str):
            if not bV:
                bV |= c == "_"
            else:
                if c.isupper() and i > 0 and enum_str[i-1] != "_":
                    result += "_"
            result += c

        return result.upper()


    def parse_custom_input(self, value:str):
        assert value[0] == "(" and value[-1] == ")"
        s = value[1:-1]
        sub_inputs = s.split("),(")
        result = []
        for i, sub in enumerate(sub_inputs):
            var_name = sub[sub.find('InputName="') + len('InputName="'):]
            var_name = var_name[: var_name.find('"')]
            if var_name:
                custom_input = unreal.CustomInput()
                custom_input.set_editor_property("InputName", var_name)
                result.append(custom_input)
        return result

    def parse_grasstype(self, value:str):
        print("parse_grasstype calls")
        assert value[0] == "(" and value[-1] == ")"
        s = value[1:-1]
        sub_inputs = s.split("),(")
        result = []
        for i, sub in enumerate(sub_inputs):
            grass_name = sub[sub.find('(Name=\"') + len('(Name=\"'):]
            grass_name = grass_name[:grass_name.find('"')]
            grass_type_path = sub[sub.find("GrassType=LandscapeGrassType'\"") + len("GrassType=LandscapeGrassType'\""):]
            grass_type_path = grass_type_path[: grass_type_path.find('"')]
            custom_input = unreal.GrassInput()

            custom_input.set_editor_property("name", grass_name)
            if grass_type_path:
                custom_input.set_editor_property("grass_type", unreal.load_asset(grass_type_path))
            result.append(custom_input)
        return result


    def parse_AttributeSetTypes(self, value: str):
        assert value[0] == "(" and value[-1] == ")"
        s = value[1:-1]
        sub_inputs = s.split(",")
        result = []
        for i, sub in enumerate(sub_inputs):
            result.append(unreal.PythonBPLib.guid_from_string(sub))
        return result

    def parse_ParameterChannelNames(self, value: str):
        assert value[0] == "(" and value[-1] == ")"
        s = value[1:-1]
        sub_inputs = s.split('),')
        result = unreal.ParameterChannelNames()
        for i, sub in enumerate(sub_inputs):
            if not sub:
                continue
            if sub.endswith(")"):
                sub = sub[:-1] # 最后一个元素会多个）, 由于替换的原因
            sub = sub[:-1]
            channel = sub[0]
            channel_name = sub[sub.rfind('"')+1:]
            result.set_editor_property(channel, channel_name)

        return result


    def get_better_value(self, property_name, cpp_type:str, value:str):
        # print(f"get_better_value call: {property_name}, {cpp_type}, {value}")
        if value == "True" or value == "False":
            return True if value == "True" else False
        if cpp_type == "FString":
            return value
        if cpp_type == "FName":
            return unreal.Name(value)
        if cpp_type == "TArray" and value == "":
            return []
        if cpp_type == "FSoftObjectPath" and value == "None":
            return unreal.SoftObjectPath()
        if cpp_type == "FParameterChannelNames":
            return self.parse_ParameterChannelNames(value)

        if cpp_type.startswith("TEnumAsByte"):
            s = cpp_type[cpp_type.find("<")+1: cpp_type.find(">")]
            if s.startswith("E"):
                s = s[1:]
            if "::Type" in s:
                s = s.replace("::Type", "")
            # print(f"!Enum: unreal.{s}.{self.trans_enum_str(value)}")
            return eval(f"unreal.{s}.{self.trans_enum_str(value)}")
        elif cpp_type == "int32" or cpp_type == "uint8" or cpp_type == "uint32":
            return int(value)
        elif cpp_type == "float":
            return float(value)
        elif cpp_type == "FLinearColor":
            m = self.linearColor_re.match(value)
            if m and m.end() - m.start() == len(value):
                v = self.linearColor_re.match(value).groups()
                v = [float(a) for a in v]
                return unreal.LinearColor(*v)
        elif cpp_type == "FVector4d":
            m = self.vector4_re.match(value)
            if m and m.end() - m.start() == len(value):
                v = [float(a) for a in m.groups()]
                v4 = unreal.Vector4d()
                for n, _v in zip(["X", "Y", "Z", "W"], v):
                    v4.set_editor_property(n, _v)
                return v4
        elif cpp_type == "FVector2D":
            m = self.vector2_re.match(value)
            if m and m.end() - m.start() == len(value):
                v = [float(a) for a in m.groups()]
                return unreal.Vector2D(*v)
        elif cpp_type == "FVector":
            m = self.vector3_re.match(value)
            if m and m.end() - m.start() == len(value):
                v = [float(a) for a in m.groups()]
                return unreal.Vector(*v)
        elif cpp_type == "LightmassSettings":
            m = self.lightmess_settings_re.match(value)
            if m and m.end() - m.start() == len(value):
                v = self.lightmess_settings_re.match(value).groups()
                v = [float(a) for a in v]
                r = unreal.LightmassMaterialInterfaceSettings()
                for name, value in zip(["EmissiveBoost", "DiffuseBoost", "ExportResolutionScale"], v):
                    if name == "EmissiveBoost" and abs(v-1) > 0.001:
                        unreal.log_warning(f"LightmassMaterialInterfaceSettings.EmissiveBoost can't be set by python, {v}")
                    else:
                        r.set_editor_property(name, value)
                return r
        elif cpp_type in {"TObjectPtr<UTexture>", "TObjectPtr<UMaterialFunctionInterface>", "TObjectPtr<UMaterialParameterCollection>"}:
            return unreal.load_asset(value[value.find("'")+1 : value.rfind("'")])
        elif cpp_type == 'FText':
            subs = value.split(", ")
            return subs[-1].strip().replace('\"', "")
        elif cpp_type == "TArray" and property_name == "ParamNames":
            if value[0] == "(" and value[-1] == ")":
                subs = value.split(", ")
                return [s.replace('\"', "") for s in subs]
        if value == "None":
            if cpp_type.startswith("TObjectPtr<"):
                if property_name == "PhysicalMaterialMap":
                    return [None]
                else:
                    return None
            return None
        if "'/Engine/" in value or "'/Game/" in value:
            asset_path = value[value.find("'")+1 : value.rfind("'")]
            return unreal.load_asset(asset_path)

        if cpp_type == "TArray" and property_name == "Inputs":
            if 'InputName=\"' in value:
                return self.parse_custom_input(value)
            else:
                return []

        if cpp_type == "TArray" and property_name == "GrassTypes"  and "GrassType=" in value:
            return self.parse_grasstype(value)

        if cpp_type == "TArray" and property_name in {"AttributeSetTypes", "AttributeGetTypes"}:
            return self.parse_AttributeSetTypes(value)


        unreal.log_error(f"Can't find property value @get_better_value : {property_name}, {cpp_type}, {value}")

    def display_name_to_ematerial_property_str(self, display_name):
        rev_dict= {  "MP_EmissiveColor": ["Final Color", "Emissive Color"]
                    , "MP_Opacity": ["Opacity"]
                    , "MP_OpacityMask": ["Opacity Mask"]
                    , "MP_DiffuseColor": ["Diffuse Color"]
                    , "MP_SpecularColor": ["Specular Color"]
                    , "MP_BaseColor": ["Albedo", "Base Color"]
                    , "MP_Metallic": ["Scatter", "Metallic"]
                    , "MP_Specular": ["Specular"]
                    , "MP_Roughness": ["Roughness"]
                    , "MP_Anisotropy":["Anisotropy"]
                    , "MP_Normal": ["Normal"]
                    , "MP_Tangent": ["Tangent"]
                    , "MP_WorldPositionOffset": ["Screen Position", "World Position Offset"]
                    , "MP_WorldDisplacement_DEPRECATED": ["World Displacement"]
                    , "MP_TessellationMultiplier_DEPRECATED": ["Tessellation Multiplier"]
                    , "MP_SubsurfaceColor": ["Extinction", "Fuzz Color", "Subsurface Color"]
                    , "MP_CustomData0": ["Clear Coat", "Backlit", "Cloth", "Iris Mask", "Curvature", "Custom Data 0"]
                    , "MP_CustomData1": ["Clear Coat Roughness", "Iris Distance", "Custom Data 1"]
                    , "MP_AmbientOcclusion": ["Ambient Occlusion"]
                    , "MP_Refraction": ["Refraction"]
                    , "MP_CustomizedUVs0": ["Customized UV 0"]
                    , "MP_CustomizedUVs1": ["Customized UV 1"]
                    , "MP_CustomizedUVs2": ["Customized UV 2"]
                    , "MP_CustomizedUVs3": ["Customized UV 3"]
                    , "MP_CustomizedUVs4": ["Customized UV 4"]
                    , "MP_CustomizedUVs5": ["Customized UV 5"]
                    , "MP_CustomizedUVs6": ["Customized UV 6"]
                    , "MP_CustomizedUVs7": ["Customized UV 7"]
                    , "MP_PixelDepthOffset": ["Pixel Depth Offset"]
                    , "MP_ShadingModel": ["Shading Model"]
                    , "MP_FrontMaterial": ["Front Material"]
                    , "MP_CustomOutput": ["Custom Output"]
                   }
        d = {v: k for k, vs in rev_dict.items() for v in vs}
        return d.get(display_name, "None")


    def create_material_from_json(self, json_obj:dict, target_path):
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        mat_name = os.path.basename(target_path)
        folder_name = os.path.dirname(target_path)
        my_mat = asset_tools.create_asset(mat_name, folder_name, unreal.Material, unreal.MaterialFactoryNew())

        # asset_tools.open_editor_for_assets([my_mat])
        # copy material property
        for grouped_value in json_obj["MaterialRoot"]["Properties"]:
            property_name = grouped_value["Name"]
            value = grouped_value["Value"]
            cpp_type = grouped_value["CppType"]

            if property_name in {"ParameterGroupData", "ThumbnailInfo", "PreviewMesh"}:
                unreal.log_warning(f"skip property: {property_name}")
                continue
            if cpp_type in {"FLightmassMaterialInterfaceSettings"}:
                unreal.log_warning(f"skip property: {property_name} of type: {cpp_type}, can't be set_editor_property")
                continue

            v = self.get_better_value(property_name, cpp_type, value)
            # print(f"{property_name} {value}, tp: {cpp_type}  --> {v} tp: {type(v)}")

            my_mat.set_editor_property(property_name, v)


        # create nodes
        created_expressions = dict()
        for exp_obj in json_obj["Expressions"]:
            index = exp_obj["Index"]
            name = exp_obj["Name"]
            path_name = exp_obj["PathName"]
            class_name = exp_obj["Class"]
            properties = exp_obj["Properties"]
            exp_type = eval(f"unreal.{class_name}")
            x = exp_obj["X"]
            y = exp_obj["Y"]
            expression = unreal.MaterialEditingLibrary.create_material_expression(my_mat, exp_type, x, y)

            created_expressions[index] = expression
            for property_obj in properties:
                p_name = property_obj["Name"]
                p_value = property_obj["Value"]
                p_type = property_obj["CppType"]

                if p_name == "AttributeSetTypes" and p_type == "TArray":
                    assert p_value[0] == "(" and p_value[-1] == ")", f"value: {value}"
                    guids_str = p_value[1:-1].split(",")
                    AttributeSetTypesNames = [property_obj[s] for s in guids_str]
                    for n in AttributeSetTypesNames:
                        unreal.PythonMaterialLib.add_input_at_expression_set_material_attributes(expression, n)
                if p_name == "AttributeGetTypes" and p_type == "TArray":
                    assert p_value[0] == "(" and p_value[-1] == ")", f"value: {value}"
                    guids_str = p_value[1:-1].split(",")
                    AttributeSetTypesNames = [property_obj[s] for s in guids_str]
                    for n in AttributeSetTypesNames:
                        unreal.PythonMaterialLib.add_output_at_expression_get_material_attributes(expression, n)

                else:
                    expression.set_editor_property(p_name, self.get_better_value(p_name, p_type, p_value ))

        print(f"Total Expressions: {len(created_expressions)}")
        # unreal.MaterialEditingLibrary.recompile_material(my_mat)

        # add connections
        for i, connection in enumerate(json_obj["Connections"][::-1]):
            # print(f"Connection: {i}")
            leftIndex = connection["LeftExpressionIndex"]
            leftOut = connection["LeftOutputIndex"]
            leftOutName = connection["LeftOutputName"]

            rightIndex = connection["RightExpressionIndex"]
            rightOut = connection["RightExpressionInputIndex"]
            rightOutName= connection["RightExpressionInputName"]

            left_output_names = unreal.PythonMaterialLib.get_material_expression_output_names(created_expressions[leftIndex])
            # print("!!! {}'s left output: {} len: {}".format(created_expressions[leftIndex].get_name(), ", ".join(left_output_names), len(left_output_names)))

            if isinstance(created_expressions[leftIndex], unreal.MaterialExpressionGetMaterialAttributes):
                ori_leftOutName = leftOutName
                leftOutName = self.display_name_to_ematerial_property_str(leftOutName)
                unreal.log(f"Change LeftOutName: {ori_leftOutName} -> {leftOutName}")

            # if rightIndex == -1:
            #     right_input_names = unreal.PythonMaterialLib.get_material_expression_input_names(created_expressions[rightIndex])
            #     print("!!! right inputs: {} len: {}".format(", ".join(right_input_names), len(right_input_names)))

            if rightIndex < 0:
                # print("Connect to Mat")
                unreal.PythonMaterialLib.connect_material_property(from_expression=created_expressions[leftIndex]
                                                                       , from_output_name=leftOutName
                                                                       , material_property_str=rightOutName)
            else:
                succ = unreal.PythonMaterialLib.connect_material_expressions(created_expressions[leftIndex], leftOutName
                                                                       , created_expressions[rightIndex], rightOutName)
                if not succ:
                    unreal.log_warning("Connect fail: {}.{} -> {}.{}".format(created_expressions[leftIndex].get_name(), leftOutName
                                                              , created_expressions[rightIndex], rightOutName))

        # unreal.MaterialEditingLibrary.layout_material_expressions(my_mat)
        unreal.MaterialEditingLibrary.recompile_material(my_mat)
        # unreal.EditorAssetLibrary.save_asset(my_mat.get_path_name())

    def on_button_RecreateByContent_click(self):
        print("on_button_RecreateByContent_click")
        ori_mat = unreal.load_asset(self.get_created_mat_path())
        if not ori_mat:
            return
        content_in_json = unreal.PythonMaterialLib.get_material_content(ori_mat)

        json_obj = json.loads(content_in_json)
        self.create_material_from_json(json_obj, "/Game/CreatedByPython/M_FromJson")

    def on_button_RecreateSelected_click(self):
        selected = Utilities.Utils.get_selected_assets()
        for sel in selected:
            if isinstance(sel, unreal.Material):
                content_in_json = unreal.PythonMaterialLib.get_material_content(sel)
                with open("d:/temp_mat.json", 'w') as f:
                    f.write(content_in_json)
                json_obj = json.loads(content_in_json)
                self.create_material_from_json(json_obj,
                                               f"/Game/CreatedByPython/CreateFromJson/{sel.get_name()}")
                # self.create_material_from_json(json_obj, f"/Game/CreatedByPython/CreateFromJson/{os.path.dirname(sel.get_path_name())}")






