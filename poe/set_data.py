import os
import json
import datetime
from os import listdir
from os.path import isfile, join
from pathlib import Path

from google.cloud import bigquery
from google.oauth2 import service_account
from google.cloud import storage


TEMP_FILE_DIR = "./temp"


def get_list():
    """get temp files
    Args:
    Returns:
        array of json file names
    """
    Path(TEMP_FILE_DIR).mkdir(parents=True, exist_ok=True)
    json_list = [f for f in listdir(TEMP_FILE_DIR) if isfile(join(TEMP_FILE_DIR, f))]
    return json_list


def get_gcp_credentials():
    """get google cloud project credentials
    Args:
    Returns:
        credentials
    """
    key = os.environ["GCP_KEY"]
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(key, strict=False)
    )
    return credentials


class Setter:
    def __init__(self):
        credentials = get_gcp_credentials()
        self.bq = bigquery.Client(
            project=os.environ["GCP_PROJECT_ID"], credentials=credentials
        )
        self.gcs = storage.Client(
            project=os.environ["GCP_PROJECT_ID"], credentials=credentials
        )
        self.current_date = datetime.datetime.now().strftime("%Y%m%d")
        self.dataset_id = "poe"

    def to_gcs(self, file_name):
        """upload files to GCS
        Args:
            temp folder's file name
        Returns:
        """
        blob_name = f"poe/{self.current_date}/" + file_name
        bucket = self.gcs.bucket(os.environ["GCS_BUCKET"])
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(f"{TEMP_FILE_DIR}/{file_name}")

    def clear(self):
        """Clear GCS folders if date < yesterday
        Args:
        Returns:
        """
        bucket = self.gcs.bucket(os.environ["GCS_BUCKET"])
        blobs = bucket.list_blobs(prefix=self.dataset_id)
        current_date_file_prefix = f"{self.dataset_id}/{self.current_date}"
        for blob in blobs:
            if (
                blob.name[: len(current_date_file_prefix)] != current_date_file_prefix
                and blob.name != f"{self.dataset_id}/"
            ):
                blob.delete()
        return True

    def to_bigquery(self):
        """GCS => Bigquery
        Args:
        Returns:
        """
        table_id = f"stashes_{self.current_date}"

        dataset = self.bq.create_dataset(self.dataset_id, exists_ok=True)
        table = bigquery.Table(dataset.table(table_id))
        config = bigquery.LoadJobConfig()

        config.write_disposition = "WRITE_TRUNCATE"
        config.source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
        # config.autodetect = True
        config.schema = [
            bigquery.SchemaField("id", "STRING"),
            bigquery.SchemaField("ts", "timestamp"),
            bigquery.SchemaField("accountName", "STRING"),
            bigquery.SchemaField("lastCharacterName", "STRING"),
            bigquery.SchemaField("stash", "STRING"),
            bigquery.SchemaField("stashType", "STRING"),
            bigquery.SchemaField("league", "STRING"),
            bigquery.SchemaField(
                "items",
                "RECORD",
                mode="REPEATED",
                fields=[
                    bigquery.SchemaField("league", "STRING"),
                    bigquery.SchemaField("id", "STRING"),
                    bigquery.SchemaField("typeLine", "STRING"),
                    bigquery.SchemaField("name", "STRING"),
                    bigquery.SchemaField(
                        "extended",
                        "RECORD",
                        mode="REPEATED",
                        fields=[
                            bigquery.SchemaField("baseType", "STRING"),
                            bigquery.SchemaField("category", "STRING"),
                            bigquery.SchemaField(
                                "subcategories", "STRING", mode="REPEATED"
                            ),
                        ],
                    ),
                    bigquery.SchemaField("implicitMods", "STRING", mode="REPEATED"),
                    bigquery.SchemaField("explicitMods", "STRING", mode="REPEATED"),
                    bigquery.SchemaField("note", "STRING"),
                    bigquery.SchemaField("verified", "BOOL"),
                    bigquery.SchemaField("icon", "STRING"),
                    bigquery.SchemaField(
                        "sockets",
                        "RECORD",
                        mode="REPEATED",
                        fields=[
                            bigquery.SchemaField("attr", "STRING"),
                            bigquery.SchemaField("group", "INT64"),
                            bigquery.SchemaField("sColour", "STRING"),
                        ],
                    ),
                    bigquery.SchemaField("progress", "INT64"),
                    bigquery.SchemaField("identified", "BOOL"),
                    bigquery.SchemaField("ilvl", "INT64"),
                    bigquery.SchemaField(
                        "properties",
                        "RECORD",
                        mode="REPEATED",
                        fields=[
                            bigquery.SchemaField("name", "STRING"),
                            bigquery.SchemaField("displayMode", "INT64"),
                            bigquery.SchemaField("type", "INT64"),
                            bigquery.SchemaField("values", "STRING"),
                        ],
                    ),
                ],
            ),
        ]
        config.ignore_unknown_values = True

        config.external_data_configuration = config
        job = self.bq.load_table_from_uri(
            f"gs://{os.environ['GCS_BUCKET']}/poe/{self.current_date}/*",
            table,
            job_config=config,
        )
        job.result()
