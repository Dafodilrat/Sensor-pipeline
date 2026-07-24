# Library Extensibility Demonstration

This document demonstrates how the filter library satisfies **Part 2, Task 3** of the assignment requirements:

> A third filter type (e.g., median filter or exponential-weighted variance estimator — your choice) must be addable by a future developer without modifying any existing `.cpp`/`.h` files in the library, only adding new ones. **Demonstrate this by actually adding one.**

> **Note**: This file has been moved from `custom_lib/filters/EXTENSIBILITY.md` to `custom_lib/EXTENSIBILITY.md` for better organization.

## Solution: Median Filter

We have added a **MedianFilter** as the third filter type that demonstrates extensibility.

### Files Added (Only New Files):

1. **`custom_lib/filters/lib/median_filter.hpp`** - The C++ MedianFilter implementation
   - Template class supporting int, float, double
   - Configurable window size (must be odd)
   - No dynamic allocations in update path
   - Type-generic implementation

2. **`custom_lib/filters/src/median_filter_bindings.cpp`** - Python bindings for MedianFilter
   - Binding functions for various types and window sizes
   - Can be included by any Python module

3. **`custom_lib/filters/src/py_median_filter_module.cpp`** - Separate Python module
   - Creates `py_median_filter` module
   - Exposes all MedianFilter variants to Python
   - **Does NOT modify any existing files**

4. **`custom_lib/running_data/lib/median_filter.hpp`** - Alternative location for running_data
   - Same implementation, available for running_data library

5. **`custom_lib/EXTENSIBILITY.md`** - This document

## running_data Library Structure

The running_data library also includes median filter support:

```
custom_lib/running_data/
├── lib/
│   ├── median_filter.hpp          # Median filter for running_data
│   └── ...
└── src/
    ├── median_filter_bindings.cpp
    └── py_median_filter_module.cpp
```

### How to Use the Median Filter:

#### In C++:
```cpp
#include "filters/lib/median_filter.hpp"

// Create a median filter with window size 5
MedianFilter<int, 5> filter;

// Update with values
int result1 = filter.update(10);
int result2 = filter.update(20);
int result3 = filter.update(30);
// ... etc
```

#### In Python:
```python
import py_median_filter

# Create a median filter
filter = py_median_filter.MedianFilterInt5()

# Update with values
result1 = filter.update(10)
result2 = filter.update(20)
result3 = filter.update(30)
# ... etc
```

### How This Demonstrates Extensibility:

1. **Zero Modifications to Existing Files**
   - No changes to `filter_bindings.cpp`
   - No changes to `py_filter_module.cpp`
   - No changes to any base filter headers
   
2. **Completely New Files Only**
   - All MedianFilter functionality is in new files
   - Existing library structure remains untouched

3. **Same Pattern for Future Filters**
   - To add a new filter (e.g., VarianceFilter):
     - Create `variance_filter.hpp` in `filters/lib/`
     - Create `variance_filter_bindings.cpp` in `filters/src/` (optional for Python)
     - Optionally create `py_variance_filter_module.cpp` for separate Python module
     - Or include bindings in existing module if preferred
   
4. **Independent Compilation**
   - The median filter can be compiled and used independently
   - Or included as part of the filters library

5. **Separate Python Module**
   - `py_median_filter` is a completely separate module
   - shows that extensions don't need to touch existing Python modules

## Verification:

Run the following to verify the median filter builds correctly:

```bash
cd custom_lib
mkdir build && cd build
cmake .. -DBUILD_TESTS=OFF
cmake --build . -j$(nproc)
```

This will produce:
- `libfilters.a` - Static library with MedianFilter
- `py_filter.<ext>` - Original filter module (unchanged)
- `py_median_filter.<ext>` - New median filter module

## Comparison with Task Requirements:

| Requirement | Implementation |
|-------------|----------------|
| Third filter type | ✅ MedianFilter |
| Addable without modifying existing .cpp/.h | ✅ Only new files added |
| Demonstrated by actually adding one | ✅ MedianFilter is added |
| Reusable | ✅ Type-generic template |
| No dynamic allocation in update path | ✅ Fixed-size array, insertion sort |
| ROS-independent | ✅ Pure C++ with no ROS dependencies |

## Architecture Notes:

The library structure follows these principles for extensibility:

1. **Header-only designs** - Filters are defined in `.hpp` files and can be used with just includes
2. **Loose coupling** - Each filter is independent and doesn't require modifying others
3. **Template-based** - Type-generic implementation works with any numeric type
4. **Separation of concerns** - Python bindings are in separate files from C++ logic

This approach allows future developers to:
- Add new filter types without touching existing code
- Extend functionality without fear of breaking changes
- Maintain clean version control history
- Test new filters independently
