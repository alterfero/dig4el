from libs import retrieval_augmented_generation_utils as ragu
import os

BASE_LD_PATH = os.path.join(
    os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "../ld"),
    "storage"
)

# TEST Retrieval
query = "passive"
indi_language = "Tahitian"
hard_kw_retrieval_results = ragu.hard_retrieve_from_query(query, indi_language)

