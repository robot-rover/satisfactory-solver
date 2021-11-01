import sys
# from .solve import optimize
# from .visualize import visualize
# from .config import load_factory

if __name__ == "__main__":
    # assert(len(sys.argv) == 2)
    # config, factories = load_factory(sys.argv[1])
    # for factory in factories:
    #     result = optimize(factory.inputs, factory.target, config)
    #     print(result)
    #     visualize(result, image_file=f"{factory.name}.png")
    from . import gui
    gui.main()
    from . import game_parse
    # game_parse.main()
