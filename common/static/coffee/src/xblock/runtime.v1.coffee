class XBlock.Runtime.v1
  children: (block) => $(block).prop('xblock_children')
  childMap: (block, childName) =>
    for child in @children(block)
        return child if child.name == childName