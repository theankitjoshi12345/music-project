# Third-party notices

## Bundled fonts

The frontend distributes unmodified Latin variable-font files from
@fontsource-variable/nunito-sans 5.3.0 and @fontsource-variable/fraunces 5.3.0.
Both use the SIL Open Font License 1.1. Their full copyright and license notices
are included in the built frontend under /font-licenses/:

- [Nunito Sans notice](frontend/public/font-licenses/nunito-sans.txt) · [Fontsource package](https://fontsource.org/fonts/nunito-sans)
- [Fraunces notice](frontend/public/font-licenses/fraunces.txt) · [Fontsource package](https://fontsource.org/fonts/fraunces)

The logo and decorative library illustration are original SVG artwork in this
repository. They are separate from imported sheet music.

## Container dependencies

The backend image installs the unmodified official Audiveris 5.11.0 Linux
package, including its bundled Java runtime and native dependencies. Audiveris
is licensed under AGPL-3.0. Its package retains the upstream license material.

- [Audiveris release and installers](https://github.com/Audiveris/audiveris/releases/tag/5.11.0)
- [Corresponding source at tag 5.11.0](https://github.com/Audiveris/audiveris/tree/5.11.0)
- [Upstream license](https://github.com/Audiveris/audiveris/blob/5.11.0/LICENSE)

The image also installs Poppler through Ubuntu's package repository. Ubuntu
package copyright and license notices remain under /usr/share/doc. Python and
JavaScript dependencies retain their installed package licenses. This notice
does not replace any dependency's license or expand the project's own license.
