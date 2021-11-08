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
    if len(sys.argv) > 1 and sys.argv[1] == 'parse':
        from . import game_parse
        game_parse.main(sys.argv[2] if len(sys.argv) > 2 else None)
    elif len(sys.argv) > 1 and sys.argv[1] == 'solve':
        from . import solve, visualize,game_parse
        result = solve.main(sys.argv[2:])
        visualize.visualize(result, game_parse.get_docs(), image_file='test.svg')
    else:
        from . import gui_qt
        gui_qt.main()
