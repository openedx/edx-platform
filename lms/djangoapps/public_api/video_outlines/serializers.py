from rest_framework import serializers

class ContentField(serializers.RelatedField):

    def iterblocks(self, start_block, categories):
        child_to_parent = {}
        stack = [start_block]

        def title_path(block):
            block_path = []
            while block in child_to_parent:
                block = child_to_parent[block]
                block_path.append(
                    {
                        'display_name': block.display_name,
                        'category': block.category,
                    }
                )
            return list(reversed(block_path))[1:-1]

        while stack:
            curr_block = stack.pop()
            if curr_block.category in categories:
                if hasattr(curr_block, "api_summary"):
                    yield {
                        "path": title_path(block),
                        "summary": curr_block.api_summary()
                    }

            if curr_block.has_children:
                for block in reversed(curr_block.get_children()):
                    stack.append(block)
                    child_to_parent[block] = curr_block



    def to_native(self, course):
        return list(self.iterblocks(course, ['video']))
