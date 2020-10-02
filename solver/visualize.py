import pygraphviz as pgv

def visualize(result, image_file=None, dot_file=None, layout='dot'):
    graph = pgv.AGraph(directed=True, strict=True, name=repr(result.target))

    resource_nodes = set()
    def new_resource(resource):
        if(resource not in resource_nodes):
            graph.add_node(resource, shape="polygon", sides=6)
            resource_nodes.add(resource)
        return resource

    input_nodes = {
        rate: f"Input:\n{rate}" for rate in result.inputs
    }

    for rate, name in input_nodes.items():
        graph.add_node(name, shape='rectangle')
        graph.add_edge(name, new_resource(rate.resource), label=f" {rate.rate} / min")

    output_nodes = {
        rate: f"Output:\n{rate}" for rate in result.outputs
    }

    for rate, name in output_nodes.items():
        graph.add_node(name, shape='rectangle')
        graph.add_edge(new_resource(rate.resource), name, label=f" {rate.rate} / min")

    recipie_nodes = [
        f"{machine} x{quantity}\n{recipie.inputs}\n{recipie.outputs}" for (machine, recipie), quantity in result.recipies.items()
    ]

    for ((machine, recipie), quantity), name in zip(result.recipies.items(), recipie_nodes):
        graph.add_node(name)
        for input in recipie.inputs:
            graph.add_edge(new_resource(input.resource), name, label=f" {input.rate * quantity} / min")

        for output in recipie.outputs:
            graph.add_edge(name, new_resource(output.resource), label=f" {output.rate * quantity} / min")

    if dot_file is not None:
        graph.write(dot_file)

    if image_file is not None:
        graph.layout(prog=layout)
        graph.draw(image_file)
