from lxml import etree 

class AnnotatableSource:
    def __init__(self, source, **kwargs):
        self._source = source
        self._annotations = []

    def render(self):
        result = { 'html': None, 'json': None }
        return result
    
    def problems(self):
        return []

    def annotations(self):
        return self.annotations

class Annotation:
    def __init__(self, target, body, **kwargs):
        self.target = target
        self.body = body
        self.problems = []

class Problem:
    def __init__(self, definition, **kwargs):
        self.definition = definition


TEXT = """
<annotatable problem_type="classification">
  <div style="float:left">
    <img src="/static/toy/images/mantony.jpg" width="300"/>
  </div>
  <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.
            <span class="annotatable" discussion="Toy_Fall_2012_Caesar0">
                Pellentesque id mauris sit amet lectus interdum tincidunt quis at mi.
                <comment title="On Lorem Ipsum">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vestibulum massa enim, sollicitudin id rutrum non, laoreet quis massa. Donec pharetra porta est id feugiat. Suspendisse aliquet cursus augue, at placerat magna adipiscing sit amet. Suspendisse velit dolor, congue in venenatis eget, consectetur pharetra massa. Vivamus facilisis tincidunt mi, nec imperdiet nibh vehicula sit amet. Donec lectus nisl, interdum sit amet faucibus et, porttitor in est.</comment>
                <problem><prompt>Instructor prompt here...</prompt><tags><tag name="foo" display_name="Foo" weight="1" answer="y"/><tag name="bar" display_name="Bar" weight="0"/><tag name="green" display_name="Green" weight="-1"/><tag name="eggs" display_name="Eggs" weight="2" answer="y"/><tag name="ham" display_name="Ham" weight="-2"/></tags><answer>Explanation here...</answer></problem>
            </span>
        Sed semper malesuada est et mattis. Mauris vel aliquet dolor. Vivamus rhoncus tristique dictum. Duis eu neque et enim euismod venenatis. Praesent porttitor commodo erat, hendrerit interdum risus sollicitudin a. Fusce neque augue, volutpat vitae vestibulum sit amet, gravida ut urna. Vivamus rutrum laoreet turpis, a gravida velit fringilla a.</p>
  <p>
            Nullam quis nisi non erat auctor tristique. Suspendisse a elit tellus. In consectetur mauris quis erat consectetur eu porta turpis sodales.
            <span class="annotatable" discussion="Toy_Fall_2012_Caesar1"><comment>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Quisque egestas aliquam dignissim. Suspendisse fringilla, ante facilisis molestie ullamcorper, nisl erat elementum orci, a convallis ante massa id tellus. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Nullam nec leo eget enim imperdiet congue eget et quam. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean a vulputate dui. Quisque gravida volutpat dolor eu porttitor. Sed varius aliquam dictum. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla dictum ligula cursus nisl volutpat consectetur. Nunc iaculis tellus orci, id aliquet purus. Sed ac justo tellus. Mauris at lacus nisi. In tincidunt nisl sit amet nisi interdum non malesuada nulla pulvinar. Aliquam scelerisque ligula ut urna fermentum tincidunt. Aenean lacinia blandit metus et interdum. Phasellus porttitor porttitor consequat. Cras ultrices dictum velit, sit amet turpis duis.</comment>
                Maecenas eu volutpat lacus.
            </span>
            Morbi luctus est
            <span class="annotatable" discussion="Toy_Fall_2012_Caesar2">
                tincidunt
                <comment title="What is this?">Ignore this for now. It's not important.</comment>
            </span>
            mauris dictum sit amet ornare augue eleifend. Quisque sagittis varius enim vulputate congue.
            <span class="annotatable" discussion="Toy_Fall_2012_Caesar3"><comment title="Lorem Ipsum TItle">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Quisque egestas aliquam dignissim. Suspendisse fringilla, ante facilisis molestie ullamcorper, nisl erat elementum orci, a convallis ante massa id tellus. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Nullam nec leo eget enim imperdiet congue eget et quam. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean a vulputate dui. Quisque gravida volutpat dolor eu porttitor. Sed varius aliquam dictum. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla dictum ligula cursus nisl volutpat consectetur. Nunc iaculis tellus orci, id aliquet purus. Sed ac justo tellus. Mauris at lacus nisi. In tincidunt nisl sit amet nisi interdum non malesuada nulla pulvinar. Aliquam scelerisque ligula ut urna fermentum tincidunt. Aenean lacinia blandit metus et interdum. Phasellus porttitor porttitor consequat. Cras ultrices dictum velit, sit amet turpis duis.</comment>
                Mauris facilisis mauris id nunc euismod vehicula. Mauris dictum nisi ac ligula posuere ultricies. Maecenas eros nisl, aliquet non eleifend ac, posuere in ante. Aliquam erat volutpat. Mauris consequat fringilla cursus. Suspendisse euismod eros et mauris imperdiet a placerat sapien semper.
            </span>
            Sed molestie laoreet magna in pharetra. Nunc mattis eleifend ultrices. Aenean ut quam vitae risus tincidunt tempor vitae sed arcu.
        </p>
  <p>
            In adipiscing metus sit amet quam sollicitudin sed suscipit diam gravida. Maecenas aliquet ante id nunc scelerisque pulvinar. Praesent ante erat, condimentum vel scelerisque non, aliquam vel urna. Cras euismod, mi at congue dignissim, velit velit aliquet est, vel vestibulum sem turpis a dui. Donec vel rutrum felis. Fusce nulla risus, volutpat sit amet molestie non, sollicitudin quis felis. Maecenas a turpis mauris. Donec vel pulvinar nulla.
            <span class="annotatable" discussion="Toy_Fall_2012_Caesar4"><comment>Chicken tenderloin boudin pig pork chop. Biltong rump frankfurter swine jowl turducken. Venison ham hock chuck pork chop, jowl chicken meatball doner meatloaf beef ribs ball tip ham. Pork drumstick fatback ribeye chicken pork chop frankfurter andouille ball tip strip steak spare ribs biltong capicola.</comment>
                Vivamus nec mi quam, non gravida erat. Fusce iaculis eros eget mi tempus vitae cursus nulla ornare. Donec a nibh purus.
            </span>
            Ut id risus quis nibh tincidunt consectetur sed ac metus. Praesent accumsan scelerisque neque, eu imperdiet justo pharetra euismod. Suspendisse potenti. Suspendisse turpis lectus, fermentum id pellentesque eu, iaculis ut tortor. Nullam ut accumsan diam.
        </p>
  <p>
    <span class="annotatable" discussion="Toy_Fall_2012_Caesar5"><comment>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Quisque egestas aliquam dignissim. Suspendisse fringilla, ante facilisis molestie ullamcorper, nisl erat elementum orci, a convallis ante massa id tellus. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Nullam nec leo eget enim imperdiet congue eget et quam. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Aenean a vulputate dui. Quisque gravida volutpat dolor eu porttitor. Sed varius aliquam dictum. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla dictum ligula cursus nisl volutpat consectetur. Nunc iaculis tellus orci, id aliquet purus. Sed ac justo tellus. Mauris at lacus nisi. In tincidunt nisl sit amet nisi interdum non malesuada nulla pulvinar. Aliquam scelerisque ligula ut urna fermentum tincidunt. Aenean lacinia blandit metus et interdum. Phasellus porttitor porttitor consequat. Cras ultrices dictum velit, sit amet turpis duis.</comment>
                Duis nisl nunc, iaculis et pretium vel, bibendum eget diam. Vestibulum consectetur facilisis pretium. Morbi tristique dui a dui tempus vitae fermentum nunc dapibus. Vestibulum bibendum nunc nec dui sollicitudin viverra. Cras quam justo, consectetur fringilla varius vitae, malesuada eu lacus. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Donec nisi lacus, feugiat sed lobortis nec, sodales sit amet tortor.
            </span>
    <span class="annotatable">
                Vestibulum lobortis mollis cursus.
                <comment>foo!</comment>
            </span>
  </p>
</annotatable>
"""

source = AnnotatableSource(TEXT)
rendered = source.render()
print ", ".join(rendered.keys()) 

