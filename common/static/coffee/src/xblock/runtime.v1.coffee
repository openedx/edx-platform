class XBlock.Runtime.v1
  children: (block) => $(block).prop('xblock_children')
  childMap: (block, childName) =>
    for child in @children(block)
        return child if child.name == childName

  # Notify the client-side runtime that an event has occurred.
  # This allows the runtime to update the UI in a consistent way
  # for different XBlocks.
  # `name` is an arbitrary string (for example, "save")
  # `data` is an object (for example, {state: 'starting'})
  # The default implementation is a no-op.
  # WARNING: This is an interim solution and not officially supported!
  notify: (name, data) -> undefined
