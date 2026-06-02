from __future__ import annotations

import argparse
import warnings
import webbrowser
from datetime import date, datetime
from typing import Any

if __package__:
    from .configuration import (
        load_sources,
        validate_bool_parameter,
        validate_date,
        validate_output_filename,
        validate_template,
    )
    from .logging_utils import (
        log_info,
        log_warn,
        print_scrape_result,
        print_scrape_status,
    )
    from .processing import (
        clean_articles,
        clean_dataframe,
        compute_tfidf,
        find_clusters,
        find_featured_clusters,
        prettify_similar,
        shuffle_content,
        write_dataframe,
    )
    from .post_processing import PostProcessingResult, run_post_processing
    from .rendering import build_html
    from .scraping import scrape_sources
else:
    from configuration import (  # type: ignore[no-redef]
        load_sources,
        validate_bool_parameter,
        validate_date,
        validate_output_filename,
        validate_template,
    )
    from logging_utils import (  # type: ignore[no-redef]
        log_info,
        log_warn,
        print_scrape_result,
        print_scrape_status,
    )
    from processing import (  # type: ignore[no-redef]
        clean_articles,
        clean_dataframe,
        compute_tfidf,
        find_clusters,
        find_featured_clusters,
        prettify_similar,
        shuffle_content,
        write_dataframe,
    )
    from post_processing import PostProcessingResult, run_post_processing  # type: ignore[no-redef]
    from rendering import build_html  # type: ignore[no-redef]
    from scraping import scrape_sources  # type: ignore[no-redef]

warnings.filterwarnings("ignore")


class NewsCollector:
    def __init__(
        self,
        sources: str = "sources.json",
        news_name: str = "Actualización diaria de noticias",
        news_date: date | str | None = None,
        template: str = "c0omposition-14.tsx",
        output_filename: str = "default",
        auto_open: bool = False,
        return_details: bool = False,
        ai_post_processing: bool = True,
        ai_post_processing_prompts_file: str | None = None,
    ) -> None:
        resolved_news_date = date.today() if news_date is None else news_date

        self.sources = Helper.load_sources(sources)
        self.news_name = news_name
        self.news_date, self.day_before = Helper.validate_date(resolved_news_date)
        self.template, self.template_path = Helper.validate_template(template)
        self.output_filename = Helper.validate_output_filename(output_filename, self.news_date)
        self.return_details = Helper.validate_return_details(return_details)
        self.auto_open = Helper.validate_auto_open(auto_open)
        self.ai_post_processing = Helper.validate_ai_post_processing(ai_post_processing)
        self.ai_post_processing_prompts_file = Helper.validate_ai_post_processing_prompts_file(
            ai_post_processing_prompts_file
        )

    def create(self) -> str | tuple[str, dict[int, list[Any]], dict[int, list[Any]]]:
        try:
            log_info(f"Starting newsletter creation for date {self.news_date}.")
            start = datetime.now()

            scraper = Scraper(self.sources, news_date=self.news_date)
            scraped_articles = scraper.scrape()

            news_df = Helper.write_dataframe(scraped_articles)
            end = datetime.now()
            Helper.print_scrape_result(news_df, start, end)

            news_df = Helper.clean_dataframe(news_df)
            news_df = Helper.clean_articles(news_df)

            tfidf_matrix, cleaned_df = Processer.compute_tfidf(news_df)
            clusters = Processer.find_clusters(cleaned_df, tfidf_matrix)
            featured_clusters = Processer.find_featured_clusters(clusters)

            if not featured_clusters:
                log_warn("No article clusters were generated. Output may be empty.")
            else:
                cluster_sizes = [len(featured_clusters[index]) for index in featured_clusters]
                log_info(
                    f"Generated {len(featured_clusters)} clusters with sizes: {cluster_sizes}"
                )

            post_result = run_post_processing(
                clusters=featured_clusters,
                news_name=self.news_name,
                news_date=self.news_date,
                enable_ai_post_processing=self.ai_post_processing,
                ai_prompts_file=self.ai_post_processing_prompts_file,
            )
            featured_clusters = post_result.clusters

            Processer.build_html(
                featured_clusters,
                self.news_name,
                self.news_date,
                self.template,
                self.output_filename,
                self.template_path,
                news_brief=post_result.news_brief,
            )
            print(
                "NewsCollector completed successfully. "
                f"View the output here: {self.output_filename}"
            )

            if self.auto_open:
                webbrowser.open(self.output_filename)

            if self.return_details:
                return self.output_filename, clusters, featured_clusters

            return self.output_filename
        except Exception as exc:
            raise RuntimeError('Error in "Newsletter.create()"') from exc


class Scraper:
    def __init__(self, sources: dict[str, dict[str, Any]], news_date: date) -> None:
        self.sources = sources
        self.news_date = news_date

    def scrape(self) -> list[dict[str, Any]]:
        try:
            return scrape_sources(self.sources, self.news_date)
        except Exception as exc:
            raise RuntimeError('Error in "Scraper.scrape()"') from exc


class Processer:
    @staticmethod
    def compute_tfidf(df: Any) -> tuple[Any, Any]:
        try:
            return compute_tfidf(df)
        except Exception as exc:
            raise RuntimeError('Error in "Processer.compute_tfidf()"') from exc

    @staticmethod
    def find_clusters(df: Any, tfidf_df: Any, distance_threshhold: float = 1) -> dict[int, list[Any]]:
        try:
            return find_clusters(
                df=df,
                tfidf_matrix=tfidf_df,
                distance_threshold=distance_threshhold,
            )
        except Exception as exc:
            raise RuntimeError('Error in "Processer.find_clusters()"') from exc

    @staticmethod
    def find_featured_clusters(clusters: dict[int, list[Any]]) -> dict[int, list[Any]]:
        try:
            return find_featured_clusters(clusters)
        except Exception as exc:
            raise RuntimeError('Error in "Processer.find_featured_clusters()"') from exc

    @staticmethod
    def build_html(
        clusters_dict: dict[int, list[Any]],
        news_name: str,
        news_date: date,
        template: str,
        output_filename: str,
        template_path: str,
        news_brief: str = "",
    ) -> bool:
        try:
            return build_html(
                clusters_dict=clusters_dict,
                news_name=news_name,
                news_date=news_date,
                template=template,
                output_filename=output_filename,
                template_path=template_path,
                news_brief=news_brief,
            )
        except Exception as exc:
            raise RuntimeError('Error in "Processer.build_html()"') from exc


class Helper:
    @staticmethod
    def log_info(message: str) -> None:
        log_info(message)

    @staticmethod
    def log_warn(message: str) -> None:
        log_warn(message)

    @staticmethod
    def validate_date(news_date: date | str) -> tuple[date, date]:
        try:
            return validate_date(news_date)
        except Exception as exc:
            raise RuntimeError('Error in "Helper.validate_date()"') from exc

    @staticmethod
    def validate_template(template: str) -> tuple[str, str]:
        try:
            return validate_template(template)
        except Exception as exc:
            raise RuntimeError('Error in "Helper.validate_template()"') from exc

    @staticmethod
    def load_sources(file_name: str) -> dict[str, Any]:
        try:
            return load_sources(file_name)
        except Exception as exc:
            raise RuntimeError('Error in "Helper.load_sources()"') from exc

    @staticmethod
    def validate_output_filename(file_name: str, news_date: date) -> str:
        try:
            return validate_output_filename(file_name, news_date)
        except Exception as exc:
            raise RuntimeError('Error in "Helper.validate_output_filename()"') from exc

    @staticmethod
    def validate_return_details(return_details: bool) -> bool:
        return validate_bool_parameter(return_details, "return_details")

    @staticmethod
    def validate_auto_open(auto_open: bool) -> bool:
        return validate_bool_parameter(auto_open, "auto_open")

    @staticmethod
    def validate_ai_post_processing(ai_post_processing: bool) -> bool:
        return validate_bool_parameter(ai_post_processing, "ai_post_processing")

    @staticmethod
    def validate_ai_post_processing_prompts_file(
        ai_post_processing_prompts_file: str | None,
    ) -> str | None:
        if ai_post_processing_prompts_file is None:
            return None

        if not isinstance(ai_post_processing_prompts_file, str):
            raise TypeError('Parameter "ai_post_processing_prompts_file" must be a string or None.')

        normalized_value = ai_post_processing_prompts_file.strip()
        if not normalized_value:
            return None

        return normalized_value

    @staticmethod
    def print_scrape_status(count: int) -> None:
        print_scrape_status(count)

    @staticmethod
    def print_scrape_result(df: Any, start: datetime, end: datetime) -> None:
        print_scrape_result(df, start, end)

    @staticmethod
    def write_dataframe(sources: list[dict[str, Any]]) -> Any:
        try:
            return write_dataframe(sources)
        except Exception as exc:
            raise RuntimeError('Error in "Helper.write_dataframe()"') from exc

    @staticmethod
    def clean_dataframe(df: Any) -> Any:
        try:
            return clean_dataframe(df)
        except Exception as exc:
            raise RuntimeError('Error in "Helper.clean_dataframe()"') from exc

    @staticmethod
    def clean_articles(df: Any) -> Any:
        try:
            return clean_articles(df)
        except Exception as exc:
            raise RuntimeError('Error in "Helper.clean_articles()"') from exc

    @staticmethod
    def shuffle_content(clusters_dict: dict[int, list[Any]]) -> None:
        try:
            shuffle_content(clusters_dict)
        except Exception as exc:
            raise RuntimeError('Error in "Helper.shuffle_content()"') from exc

    @staticmethod
    def prettify_similar(clusters_dict: dict[int, list[Any]]) -> dict[int, dict[str, list[str]]]:
        try:
            return prettify_similar(clusters_dict)
        except Exception as exc:
            raise RuntimeError('Error in "Helper.prettify_similar()"') from exc


def _parse_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value

    normalized = value.strip().lower()
    truthy_values = {"1", "true", "t", "yes", "y", "on"}
    falsy_values = {"0", "false", "f", "no", "n", "off"}

    if normalized in truthy_values:
        return True
    if normalized in falsy_values:
        return False

    raise argparse.ArgumentTypeError(f'Expected a boolean value, got "{value}".')


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Automated News Article Collection with Python"
    )
    parser.add_argument(
        "-s",
        "--sources",
        type=str,
        required=False,
        default="sources.json",
        help="Path of source JSON file with news sources to be scraped.",
    )
    parser.add_argument(
        "-n",
        "--news_name",
        type=str,
        required=False,
        default="Actualización diaria de noticias",
        help="Title name of the newsletter.",
    )
    parser.add_argument(
        "-d",
        "--news_date",
        type=str,
        required=False,
        default=str(date.today()),
        help="Date of the newsletter in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "-t",
        "--template",
        type=str,
        required=False,
        default="c0omposition-14.tsx",
        help="Filename of the template HTML newsletter file.",
    )
    parser.add_argument(
        "-o",
        "--output_filename",
        type=str,
        required=False,
        default="default",
        help="Filename of the output HTML newsletter file.",
    )
    parser.add_argument(
        "-r",
        "--return_details",
        type=_parse_bool,
        required=False,
        default=False,
        help="Choose whether to return the collected cluster data.",
    )
    parser.add_argument(
        "-a",
        "--auto_open",
        type=_parse_bool,
        required=False,
        default=False,
        help="Choose whether to automatically open the newsletter in the browser.",
    )
    parser.add_argument(
        "--ai_post_processing",
        type=_parse_bool,
        required=False,
        default=True,
        help="Choose whether to apply AI post-processing with OpenRouter.",
    )
    parser.add_argument(
        "--ai_post_processing_prompts_file",
        type=str,
        required=False,
        default=None,
        help=(
            "Optional path to AI post-processing prompt config JSON file. "
            "Defaults to newscollector/post_processing/ai_post_processing/prompts.json"
        ),
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    newsletter = NewsCollector(
        sources=args.sources,
        news_name=args.news_name,
        news_date=args.news_date,
        template=args.template,
        output_filename=args.output_filename,
        auto_open=args.auto_open,
        return_details=args.return_details,
        ai_post_processing=args.ai_post_processing,
        ai_post_processing_prompts_file=args.ai_post_processing_prompts_file,
    )
    newsletter.create()


if __name__ == "__main__":
    main()


__all__ = ["NewsCollector", "Scraper", "Processer", "Helper", "main"]
