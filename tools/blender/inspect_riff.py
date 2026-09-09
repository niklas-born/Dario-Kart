import bpy
for node in bpy.data.materials['Riff | turquoise skin'].node_tree.nodes:
    if node.type == 'BSDF_PRINCIPLED':
        print('BSDF_INPUTS', [(v.name, str(v.default_value)) for v in node.inputs if hasattr(v, 'default_value')])
for mat in bpy.data.materials:
    if mat.use_nodes:
        node = mat.node_tree.nodes.get('Principled BSDF')
        if node:
            print(mat.name, 'base', tuple(node.inputs['Base Color'].default_value),
                  'rough', node.inputs['Roughness'].default_value,
                  'sss', node.inputs['Subsurface Weight'].default_value)
for name in ['Riff_Skin','Eye_L','Upper_Lid_L','Horn_L','Iris_L']:
    obj=bpy.data.objects[name]
    print(name, list(obj.dimensions), [m.name if m else None for m in obj.data.materials],
          'materials used', sorted(set(p.material_index for p in obj.data.polygons)))
    if obj.data.shape_keys:
        print('keys',[(k.name,k.value) for k in obj.data.shape_keys.key_blocks])
        print('basis z',min(v.co.z for v in obj.data.shape_keys.key_blocks[0].data),max(v.co.z for v in obj.data.shape_keys.key_blocks[0].data))
