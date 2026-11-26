select feature_id, feature_name, feature_area
from {{ ref('stg_product__features') }}
