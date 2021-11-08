import pygraphviz as pgv

def visualize(result, game_data, image_file=None, dot_file=None, layout='dot'):
    graph = pgv.AGraph(directed=True, strict=True, name=repr(result.problem.target))

    resource_nodes = set()
    def new_resource(resource):
        if(resource not in resource_nodes):
            graph.add_node(resource, shape="polygon", sides=6, label=game_data.items[resource])
            resource_nodes.add(resource)
        return resource

    input_nodes = {
        rate: f"Input:\n{rate.format(game_data)}" for rate in result.problem.inputs
    }

    for rate, name in input_nodes.items():
        graph.add_node(name, shape='rectangle')
        graph.add_edge(name, new_resource(rate.resource), label=f" {rate.rate} / min")

    output_nodes = {
        rate: f"Output:\n{rate.format(game_data)}" for rate in result.outputs
    }

    for rate, name in output_nodes.items():
        graph.add_node(name, shape='rectangle')
        graph.add_edge(new_resource(rate.resource), name, label=f" {rate.rate} / min")

    print(result.recipes)
    recipes = {game_data.recipes[recipe_id]: quantity for recipe_id, quantity in result.recipes.items()}

    for recipe, quantity in recipes.items():
        machine_name = game_data.machines[recipe.machine].display
        inputs = ','.join(
            rate.format(game_data) for rate in recipe.input_rates()
        )

        outputs = ','.join(
            rate.format(game_data) for rate in recipe.output_rates()
        )

        name = f"{machine_name} x{quantity}\n{inputs}\n{outputs}"
        graph.add_node(recipe.id, label=name)
        for ir in recipe.input_rates():
            graph.add_edge(new_resource(ir.resource), recipe.id, label=f" {ir.rate * quantity} / min")

        for ir in recipe.output_rates():
            graph.add_edge(recipe.id, new_resource(ir.resource), label=f" {ir.rate * quantity} / min")

    if dot_file is not None:
        graph.write(dot_file)

    if image_file is not None:
        graph.layout(prog=layout)
        graph.draw(image_file)
