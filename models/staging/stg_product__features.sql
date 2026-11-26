select feature_id, feature_name, feature_area
from {{ source('raw', 'product_features') }}
