# seangrogan.github.io

My GitHub Pages site. Edit these files on github.com (open the file, click the pencil, change it, commit). GitHub rebuilds the site in a minute or two.

| To change…                    | Edit                  |
| ----------------------------- | --------------------- |
| The name and the line under it | `_config.yml`        |
| The introduction              | `index.md`            |
| Projects and their sections   | `_data/projects.yml`  |
| The "Elsewhere" links         | `_data/profiles.yml`  |

Each `.yml` file has instructions at the top. Order in the file is order on the page.

The contour map behind the name is `assets/contours.svg`. To make it stronger, fainter or sharper, change `--contour-opacity` and `--contour-blur` near the top of `_layouts/home.html`. To use a different map, replace the file with a line drawing that has a transparent background: the lines can be any colour, but any filled background shape will cover the whole sign.

`_layouts/home.html` is the page design. You shouldn't need to touch it to change content.
