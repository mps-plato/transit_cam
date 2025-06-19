from argparse import ArgumentParser
from pathlib import Path


from transit_cam.executables.shared_logging_setup_for_executables import init_logging
from transit_cam.analysis.analyzer import AnalyzeFileArgs, Analyzer


def main():
    parser = ArgumentParser(description='Analyze and plot light curves')
    parser.add_argument(
        '-n', '--n-last-files',
        type=int,
        default=1,
        help='number of files to be analyzed',
        required=False
    )
    parser.add_argument(
        '-p', '--planet-name',
        action='store', type=str,
        help='name of the planet', default='MPS'
    )
    parser.add_argument(
        "--log",
        choices=["debug", "info", "warning", "error"],
        default="info",
        dest="log_level"
    )

    args = parser.parse_args()

    init_logging(args.log_level)
    files: list[Path] = sorted(Path("transit_cam_records").glob("*"))
    analyzer = Analyzer()
    for filename in files[-args.n_last_files:]:
        print("-"*30)
        analyzer.analyze_file(
            AnalyzeFileArgs(
                filename,
                planet_name=args.planet_name
            )
        )


if __name__ == '__main__':
    main()
