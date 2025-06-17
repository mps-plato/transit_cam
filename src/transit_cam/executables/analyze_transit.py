from argparse import ArgumentParser
from pathlib import Path


from transit_cam.analysis.analyzer import AnalyzeFileArgs, Analyzer

    
def main():
    parser = ArgumentParser(description='Analyze and plot light curves')
    parser.add_argument(
        '--n-last-files', 
        type=int, 
        default=1, 
        help='number of files to be analyzed',
        required=False
    )
    parser.add_argument(
        '-np', '--no_pdf', 
        action='store_true', 
        help='skip PDF export'
    )
    parser.add_argument(
        '-c', '--count', 
        action='store', type=int, default=1,
        help='number of light curves to analyze (0 for all)'
    )
    parser.add_argument(
        '-n', '--planet_name', 
        action='store', type=str, 
        help='name of the planet', default='MPS'
    )

    args = parser.parse_args()

    files: list[Path] = sorted(Path("transit_cam_records").glob("*"))
    analyzer = Analyzer()
    for filename in files[-args.n_last_files:]:
        analyzer.analyze_file(
            AnalyzeFileArgs(
                filename,
                create_pdf=not args.no_pdf,
                number_of_lightcurves=args.count,
                planet_name=args.planet_name
            )
        )


if __name__ == '__main__':
    main()
