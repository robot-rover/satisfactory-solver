import pygraphviz as pgv


def visualize(result, game_data, image_file=None, dot_file=None, layout='dot'):
    graph = pgv.AGraph(directed=True, strict=True,
                       name=repr(result.problem.target))

    resource_nodes = set()

    def new_resource(resource_id):
        if(resource_id not in resource_nodes):
            resource = game_data.items[resource_id]
            graph.add_node(resource_id, shape="hexagon",
                           label=resource.display)
            resource_nodes.add(resource_id)
        return resource_id

    input_nodes = {
        rate: f"Input:\n{rate.format(game_data)}" for rate in result.problem.inputs
    }

    for rate, name in input_nodes.items():
        graph.add_node(name, shape='rectangle')
        graph.add_edge(name, new_resource(rate.resource),
                       label=f" {round(rate.rate, 3)} / min")

    output_nodes = {
        rate: f"Output:\n{rate.format(game_data)}" for rate in result.outputs
    }

    for rate, name in output_nodes.items():
        graph.add_node(name, shape='rectangle')
        graph.add_edge(new_resource(rate.resource),
                       name, label=f" {round(rate.rate, 3)} / min")

    recipes = {game_data.recipes[recipe_id]: quantity for recipe_id, quantity in result.recipes.items()}

    for recipe, quantity in recipes.items():
        machine_name = game_data.machines[recipe.machine].display
        inputs = ', '.join(
            f'{game_data.items[rate.resource].display}: {rate.rate}' for rate in recipe.input_rates()
        )

        outputs = ', '.join(
            f'{game_data.items[rate.resource].display}: {rate.rate}' for rate in recipe.output_rates()
        )

        name = f"{recipe.display}\n{machine_name} x{round(quantity, 3)}\n{inputs}\n{outputs}"
        graph.add_node(recipe.id, label=name)
        for ir in recipe.input_rates():
            graph.add_edge(new_resource(ir.resource), recipe.id,
                           label=f" {round(ir.rate * quantity, 3)} / min")

        for ir in recipe.output_rates():
            graph.add_edge(recipe.id, new_resource(ir.resource),
                           label=f" {round(ir.rate * quantity, 2)} / min")

    if dot_file is not None:
        graph.write(dot_file)

    if image_file is not None:
        graph.layout(prog=layout)
        graph.draw(image_file)
