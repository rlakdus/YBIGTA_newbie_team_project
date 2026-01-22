import sys
from pathlib import Path

# 현재 파일(main.py) 기준으로 루트 경로를 잡고 sys.path에 추가합니다.
FILE_PATH = Path(__file__).resolve()
ROOT_DIR = FILE_PATH.parent.parent.parent
sys.path.append(str(ROOT_DIR))

# glob이 사용하는 상대 경로("../../")가 터미널 실행 위치에 상관없이 항상 'ROOT_DIR'를 가리키도록 작업 경로(CWD)를 강제 변경
import os
os.chdir(FILE_PATH.parent)

import glob
from argparse import ArgumentParser
from typing import Dict, Type
from review_analysis.preprocessing.base_processor import BaseDataProcessor
from review_analysis.preprocessing.yes24_processor import Yes24Processor

# 모든 preprocessing 클래스를 예시 형식으로 적어주세요. 
# key는 "reviews_사이트이름"으로, value는 해당 처리를 위한 클래스
PREPROCESS_CLASSES: Dict[str, Type[BaseDataProcessor]] = {
    "reviews_yes24": Yes24Processor,
    # key는 크롤링한 csv파일 이름으로 적어주세요! ex. reviews_naver.csv -> reviews_naver
}

REVIEW_COLLECTIONS = glob.glob(os.path.join("..","..","database", "reviews_*.csv"))

def create_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument('-o', '--output_dir', type=str, required=False, default = "../../database", help="Output file dir. Example: ../../database")
    parser.add_argument('-c', '--preprocessor', type=str, required=False, choices=PREPROCESS_CLASSES.keys(),
                        help=f"Which processor to use. Choices: {', '.join(PREPROCESS_CLASSES.keys())}")
    parser.add_argument('-a', '--all', action='store_true',
                        help="Run all data preprocessors. Default to False.")    
    return parser

if __name__ == "__main__":

    parser = create_parser()
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    if args.all: 
        for csv_file in REVIEW_COLLECTIONS:
            base_name = os.path.splitext(os.path.basename(csv_file))[0]
            if base_name in PREPROCESS_CLASSES:
                preprocessor_class = PREPROCESS_CLASSES[base_name]
                preprocessor = preprocessor_class(csv_file, args.output_dir)
                preprocessor.preprocess()
                preprocessor.feature_engineering()
                preprocessor.save_to_database()
