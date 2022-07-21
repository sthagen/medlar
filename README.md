# mapology

Simple python filters generating leaflet driven apps.


## Installation

`pip install mapology`

## Usage Notes

Currently there are some dependencies across env var values. A working example is below:

```
GEO_FOOTER_HTML_CONTENT='<p><small><a href="mailto:some.contact@example.com">Some Contact, YES</a></small></p>'
GEO_BASE_URL="https://example.com"
GEO_LIB_PATH="/ndb/_/leaflet"
GEO_PATH_NAV="/ndb/43"
GEO_PREFIX_PATH="${GEO_PATH_NAV}/prefix"
export GEO_FOOTER_HTML_CONTENT
export GEO_BASE_URL
export GEO_LIB_PATH
export GEO_PATH_NAV
export GEO_PREFIX_PATH
```

## Status

Experimental.


**Note**: The name of the default branch is `default`.
