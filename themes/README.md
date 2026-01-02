## Themes

Esta pasta contém apenas os pacotes de temas e assets.

Consulte o [README principal do projeto](../README.md) para instruções de uso e integração.
		"mascot": {
			"frames": ["characters/m0.png", "characters/m1.png"],
			"fps": 8
		}
	}
}
```


```json
{
	"characters": {
		"mascot": {
			"sheet": "characters/enemies_sheet.png",
			"tileSize": 8,
			"scale": 2,
			"colorKey": "#5C94FC",
			"fps": 8,
			"frames": [
				{
					"parts": [
						{ "tx": 1, "ty": 2, "tw": 2, "th": 2, "dx": 0, "dy": 0 }
					]
				},
				{
					"parts": [
						{ "x": 16, "y": 32, "w": 16, "h": 16, "dx": 0, "dy": 0 }
					]
				}
			]
		}
	}
}
```

Notes:
- Use `tx/ty/tw/th` for tile coordinates (multiplied by `tileSize`, default 8).
- Use `x/y/w/h` for pixel coordinates.
- `dx/dy` is where the part is placed inside the frame.
- Optional: `flipX`, `flipY` in a part.

### Random enemy each page load (variants)
To randomize the mascot/enemy every time `/monitor` loads, define `variants` and set `random: true`.
You can force a specific one with `?enemy=<name>`.

```json
{
	"characters": {
		"mascot": {
			"sheet": "characters/enemies_sheet.png",
			"tileSize": 8,
			"scale": 2,
			"colorKey": "#5C94FC",
			"random": true,
			"variants": {
				"goomba": {
					"frames": [
						{ "parts": [{ "tx": 0, "ty": 0, "tw": 2, "th": 2, "dx": 0, "dy": 0 }] },
						{ "parts": [{ "tx": 2, "ty": 0, "tw": 2, "th": 2, "dx": 0, "dy": 0 }] }
					],
					"fps": 8
				},
				"koopa": {
					"frames": [
						{ "parts": [{ "tx": 0, "ty": 2, "tw": 2, "th": 2, "dx": 0, "dy": 0 }] },
						{ "parts": [{ "tx": 2, "ty": 2, "tw": 2, "th": 2, "dx": 0, "dy": 0 }] }
					],
					"fps": 10
				}
			}
		}
	}
}
```


