import sys
from pathlib import Path
import os
import glob
from argparse import ArgumentParser
from typing import Dict, Type

# 프로젝트 최상위 루트 경로 확보
# 현재 파일(main.py)의 상위(preprocessing) -> 상위(review_analysis) -> 상위(프로젝트루트)
FILE_PATH = Path(__file__).resolve()
ROOT_DIR = FILE_PATH.parent.parent.parent 
sys.path.append(str(ROOT_DIR))

from review_analysis.preprocessing.base_processor import BaseDataProcessor
from review_analysis.preprocessing.ridibooks_processor import RidibooksProcessor
from review_analysis.preprocessing.kyobo_processor import KyoboProcessor
from review_analysis.preprocessing.yes24_processor import Yes24Processor


# 모든 preprocessing 클래스를 예시 형식으로 적어주세요. 
# key는 "reviews_사이트이름"으로, value는 해당 처리를 위한 클래스
PREPROCESS_CLASSES: Dict[str, Type[BaseDataProcessor]] = {
    "reviews_ridibooks": RidibooksProcessor,
    "reviews_kyobo": KyoboProcessor,
    "reviews_yes24": Yes24Processor
    # key는 크롤링한 csv파일 이름으로 적어주세요! ex. reviews_naver.csv -> reviews_naver
}

# ROOT_DIR를 기준으로 절대 경로로 찾기
REVIEW_COLLECTIONS = glob.glob(os.path.join(ROOT_DIR, "database", "reviews_*.csv"))

def create_parser() -> ArgumentParser:
    parser = ArgumentParser()
    
    # 저장 경로 기본값: ROOT_DIR 기준 'database' 폴더 절대 경로
    default_out_path = os.path.join(ROOT_DIR, "database")
    
    parser.add_argument('-o', '--output_dir', type=str, required=False, default=default_out_path, 
                        help="Output file dir.")
    parser.add_argument('-c', '--preprocessor', type=str, required=False, choices=PREPROCESS_CLASSES.keys(),
                        help=f"Which processor to use. Choices: {', '.join(PREPROCESS_CLASSES.keys())}")
    parser.add_argument('-a', '--all', action='store_true',
                        help="Run all data preprocessors.")    
    return parser

if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()

    # 입력받은 경로를 절대 경로로 확정
    final_output_dir = os.path.abspath(args.output_dir)
    os.makedirs(final_output_dir, exist_ok=True)

    # 전체 실행 (-a)
    if args.all: 
        if not REVIEW_COLLECTIONS:
            print(f"Error: No csv files found in {os.path.join(ROOT_DIR, 'database')}")
            sys.exit(1)

        for csv_file in REVIEW_COLLECTIONS:
            base_name = os.path.splitext(os.path.basename(csv_file))[0]
            if base_name in PREPROCESS_CLASSES:
                print(f"--- Processing: {base_name} ---")
                Processor_class = PREPROCESS_CLASSES[base_name]
                # 절대 경로로 변환된 final_output_dir 전달
                processor = Processor_class(csv_file, final_output_dir)
                processor.preprocess()
                processor.feature_engineering()
                processor.save_to_database()

    # 특정 사이트 실행 (-c)
    elif args.preprocessor:
        # 파일 경로도 ROOT_DIR 기준으로 찾아서 생성
        target_csv = os.path.join(ROOT_DIR, "database", f"{args.preprocessor}.csv")
        
        if os.path.exists(target_csv):
            print(f"--- Processing Single: {args.preprocessor} ---")
            Processor_class = PREPROCESS_CLASSES[args.preprocessor]
            processor = Processor_class(target_csv, final_output_dir)
            processor.preprocess()
            processor.feature_engineering()
            processor.save_to_database()
        else:
            print(f"Error: File not found -> {target_csv}")
    