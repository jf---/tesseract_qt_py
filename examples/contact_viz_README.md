# Contact Visualization

Contact/collision results visualization for tesseract_qt_py.

## Features

1. **Contact Points**: Small red spheres at collision points
2. **Contact Normals**: Green arrows showing collision normals
3. **Link Highlighting**: Orange coloring for links in collision
4. **Clear Visualization**: Remove all contact markers

## Usage

### Basic Example

```python
from tesseract_robotics.tesseract_collision import ContactRequest, ContactResultMap, ContactResultVector, ContactTestType_ALL
from tesseract_robotics.tesseract_common import CollisionMarginData

# Get discrete contact manager
manager = env.getDiscreteContactManager()
manager.setActiveCollisionObjects(env.getActiveLinkNames())

# Set collision margin
margin = CollisionMarginData(0.0)
manager.setCollisionMarginData(margin)

# Update transforms
state = env.getState()
manager.setCollisionObjectsTransform(state.link_transforms)

# Execute collision check
result_map = ContactResultMap()
manager.contactTest(result_map, ContactRequest(ContactTestType_ALL))

# Flatten results
results = ContactResultVector()
result_map.flattenMoveResults(results)

# Visualize
scene_manager.visualize_contacts(results)

# Clear when done
scene_manager.clear_contacts()
```

### Run Demo

```bash
cd tesseract_qt_py
python examples/contact_viz_example.py /path/to/robot.urdf /path/to/robot.srdf
```

## API

### SceneManager Methods

- `visualize_contacts(contact_results)`: Visualize ContactResultVector from tesseract
- `clear_contacts()`: Remove all contact visualization

### ContactVisualizer Methods

- `visualize_contacts(contact_results, link_actors)`: Main visualization method
- `clear()`: Clear all contact markers and restore link colors
- `_add_contact_point(point, radius, color)`: Add contact point marker
- `_add_contact_normal(point, normal, scale, color)`: Add normal arrow
- `_highlight_link(link_name, actors, color)`: Highlight colliding link

## Contact Result Structure

Expected from `tesseract_robotics.tesseract_collision.ContactResult`:

- `nearest_points`: List of contact point coordinates (3D)
- `normal`: Contact normal vector (3D)
- `link_names`: Pair of colliding link names
- `distance`: Penetration distance (negative for collision)
