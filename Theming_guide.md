# Framework Hub Mini - Theming Guide

This guide explains how to customize the appearance of Framework Hub Mini through its theme system. The application comes with three built-in themes that you can use as references for creating your own:
- `default_theme.json`: A modern dark theme with orange accents
- `fedora_dark_theme.json`: A GNOME-inspired dark theme with blue accents
- `fedora_light_theme.json`: A clean light theme based on GNOME

## Theme Structure

Each theme is defined in a JSON file with the following structure:

```json
{
    "name": "Theme Name",
    "colors": {
        // Color definitions
    },
    "fonts": {
        // Font settings
    },
    "spacing": {
        // Spacing values
    },
    "radius": {
        // Border radius values
    }
}
```

## Color Configuration

### Primary Colors
```json
"primary": "#FF7043",    // Main accent color used throughout the UI
"hover": "#F4511E"       // Color used when hovering over interactive elements
```

### Background Colors
```json
"background": {
    "main": "#1E1E1E",       // Main window background
    "secondary": "#2D2D2D",   // Secondary elements background
    "tertiary": "#383838",    // Tertiary elements background
    "header": "#1E1E1E",      // Header sections background
    "input": "#2D2D2D"        // Input fields background
}
```

### Text Colors
```json
"text": {
    "primary": "#FFFFFF",     // Main text color
    "secondary": "#E0E0E0",   // Secondary text color
    "disabled": "#A0A0A0",    // Disabled text color
    "accent": "#FF7043"       // Accent text color
}
```

### Border Colors
```json
"border": {
    "active": "#FFFFFF",      // Active element borders
    "inactive": "#404040",    // Inactive element borders
    "input": "#FF7043"        // Input field borders
}
```

### Button Colors
```json
"button": {
    "primary": "#FF7043",     // Primary button color
    "secondary": "#2D2D2D",   // Secondary button color
    "disabled": "#404040",    // Disabled button color
    "danger": "#FF4444",      // Danger/Delete button color
    "success": "#4CAF50",     // Success button color
    "warning": "#FFC107"      // Warning button color
}
```

### Progress Bar Colors
```json
"progress": {
    "background": "#2D2D2D",  // Progress bar background
    "bar": "#FF7043",         // Default progress bar color
    "cpu": "#FF7043",         // CPU usage bar color
    "gpu": "#00BCD4",         // GPU usage bar color
    "ram": "#4CAF50",         // RAM usage bar color
    "temp": "#FFC107"         // Temperature bar color
}
```

### Status Colors
```json
"status": {
    "error": "#FF4444",       // Error status color
    "warning": "#FFC107",     // Warning status color
    "success": "#4CAF50",     // Success status color
    "info": "#2196F3"         // Information status color
}
```

### Scrollbar Colors
```json
"scrollbar": {
    "background": "#2D2D2D",  // Scrollbar track background
    "thumb": "#FF7043",       // Scrollbar thumb color
    "hover": "#F4511E"        // Scrollbar thumb hover color
}
```

## Font Configuration

```json
"fonts": {
    "main": {
        "family": "Roboto",   // Main font family
        "size": {
            "small": 10,      // Small text size
            "normal": 11,     // Normal text size
            "large": 12,      // Large text size
            "title": 14       // Title text size
        }
    },
    "monospace": {
        "family": "Consolas", // Monospace font family (for code/logs)
        "size": {
            "small": 10,
            "normal": 11,
            "large": 12,
            "title": 14
        }
    }
}
```

## Spacing and Radius

### Spacing
```json
"spacing": {
    "small": 5,      // Small gaps between elements
    "normal": 10,    // Normal padding and margins
    "large": 20      // Large spacing for sections
}
```

### Border Radius
```json
"radius": {
    "small": 5,      // Subtle rounded corners
    "normal": 10,    // Standard button/widget corners
    "large": 15      // Large container corners
}
```

## Creating Your Own Theme

1. **Start with a Template**
   - Copy one of the existing theme files
   - Rename it to `your_theme_name.json`
   - Place it in the `configs` directory

2. **Customize Colors**
   - Choose a primary color that will define your theme's identity
   - Create a cohesive color palette around your primary color
   - Ensure sufficient contrast between text and background colors
   - Test different states (hover, active, disabled)

3. **Font Selection**
   - Choose readable fonts for both main text and monospace content
   - Adjust font sizes based on your needs
   - Ensure fonts are widely available or include them with your theme

4. **Fine-tune Spacing and Radius**
   - Adjust spacing values to create comfortable layouts
   - Set border radius values to match your desired style (sharp or rounded)

## Best Practices

1. **Color Contrast**
   - Maintain a minimum contrast ratio of 4.5:1 for text readability
   - Test your theme with the color blindness simulator
   - Ensure interactive elements are clearly distinguishable

2. **Consistency**
   - Use similar hues for related elements
   - Maintain consistent spacing throughout the interface
   - Keep font sizes proportional

3. **Testing**
   - Test your theme in different lighting conditions
   - Verify all UI elements are visible and usable
   - Check how your theme looks in different sections of the application

## Example: Creating a Purple Dark Theme

```json
{
    "name": "Purple Dark",
    "colors": {
        "primary": "#9C27B0",
        "hover": "#BA68C8",
        "background": {
            "main": "#1A1A1A",
            "secondary": "#2D2D2D",
            "tertiary": "#383838",
            "header": "#1A1A1A",
            "input": "#2D2D2D"
        },
        "text": {
            "primary": "#FFFFFF",
            "secondary": "#E0E0E0",
            "disabled": "#9E9E9E",
            "accent": "#CE93D8"
        }
        // ... rest of the color configuration
    }
    // ... fonts, spacing, and radius configuration
}
```

## Troubleshooting

1. **Theme Not Loading**
   - Verify JSON syntax is valid
   - Check file is in the correct directory
   - Ensure file permissions are correct

2. **Colors Look Wrong**
   - Verify color codes are in correct format (#RRGGBB)
   - Check contrast ratios
   - Test in different lighting conditions

3. **Font Issues**
   - Verify font family names are correct
   - Ensure fonts are installed on the system
   - Check font size values are reasonable

Remember to share your themes with the community if you create something awesome! You can contribute them back to the project through a pull request. 