# Changes

## [5.0.0](https://github.com/krux/python-krux-stdlib/tree/5.0.0)

### Summary
Drops support for Python versions lower than 3.6.

**New Features**
- `@util.cache()`: A caching decorator with optional expiration in seconds.
- `@util.cache_wrapper`: The non-decorator version of `@util.cache()`.

**Breaking Changes**
- Python 2 is no longer supported.
- Python versions lower than 3.6 are no longer supported.
