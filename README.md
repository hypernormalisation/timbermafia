# timbermafia

![](static/demo0.png)

`timbermafia` is a drop-in replacement for application logging in
python, supporting 256-bit colour output over aligned columns and expanded
formatting options.

Users can choose from a selection of predefined styles and colour
palettes, or can easily make their own.

## Installation

`timbermafia` is available on the Python Package Index (PyPI).
```bash
pip install timbermafia
```
It requires python version 3.6 or later.

## Basic usage

You can get started using timbermafia with a simple:
```python
import timbermafia as tm
tm.basic_config()
```
placed in your script or application. This configuration function is
very flexible, and can be used to specify styles, colour palettes,
logging and date formats, output streams or files, and more.

`timbermafia.basic_config` is by default similar to
`logging.basicConfig`, in that it modifies the logging module's root
logger. This may not be what you want: for instance, every library with
logging calls in your application will produce output!

To prevent this, instead produce a named `logging.Logger` object by
passing the `name` keyword to the function, and retrieve it later with
`logging.getLogger`.

## Try it out!

Once installed with `pip`, a script called `demo_timbermafia` is placed
in the user's bin. The user can specify a style, colour palette, and
logging format to be used:

![](static/demo1.png)

The available styles and colour palettes can be shown with

```python
import timbermafia as tm
tm.print_styles()
tm.print_palettes()
```

## Advanced usage
The `timbermafia.basic_config` function is fairly flexible, and should
cover most use cases for configuring logging to streams and files.

If you have a specific logging requirement for other logging handlers,
or require a more fine control of handler levels, you can acquire an
instance of the custom formatter with something like:

```python
import timbermafia as tm
f = tm.get_timbermafia_formatter(style='compact', palette='ocean')
```

and use the formatter in your own logging handlers.

## Titles in logging

Timbermafia supports monkey patching of the `logging.Logger` class to
enable any Logger object to print a title with a divider to the output.

To enable this run

```python
import timbermafia as tm
tm.monkey_patch_logger()
```

and then from any logger do e.g.:

```python
import logging
log = logging.getLogger()
log.header('My title')
log.info('You can separate your output into sections.')
log.debug('Titles respect colour schemes.')
```

to produce the following in your logging output.

![](static/demo4.png)

## Formats

`timbermafia` expands what is possible in a logging format, adding
support for a variety of features.

### Vertically-aligned columns.

The user can specify columns to be used in the output, which for long
messages, names, function names etc. can be used to print legible
multi-line output.

The column widths adapt based on what fields are present in them, so
columns containing a high amount of output get more room.

An example format using 4 columns, containing respectively the:
- date/time
- level name
- process name and log name
- log message

can be specified with a column escape, by default "_". Whatever follows
the column escape until the next whitespace is registered as output that
will visually separate the column.

So our format can be e.g.

```
{asctime} _| {levelname} _| {processName} {name}  __:: {message}
```

which produces the following output with the "synth" colour palette:

![](static/demo2.png)

Note that we double-escape the final separator so that it prints over
all lines of multi-line output, and that multiple characters, or indeed
no characters, can be used as a column separator.

### Enhanced fmt_spec

Individual log records can be formatted according to a format
specification, or fmt_spec.

For example, the following output will force the message content to be
bold and bright green, overriding any formatting based upon the log
level, and underline the time to punctuate the start of a new log
record:

```
{asctime:u} _ {name} _ {message:b,>82}
```

Let's try that out with the "ocean" palette:

![](static/demo3.png)

The following are recognised in the format spec via a comma-separated
list:
- b: bold
- e: emphasis/italic
- u: underline
- any int: the corresponding ANSI code, e.g. 5,9 will set slow blink and
  crossed-out text
- \>int: set the foreground colour to the 8-bit colour code.
- \<int: set the background colour to the 8-bit colour code.

Note that what ANSI codes will be possible is dependent on what terminal
or terminal emulator is being used.

A full list of the ANSI colour codes matched to some sample output can
be printed to the terminal with the included script
`display_ansi_colours`.

## Custom styles and palettes

Each style and palette can be generated into a Style or Palette object,
with a flexible customisation supported.

A full guide to customising styles and palettes can be found in [this
notebook](notebooks/styles_and_palettes.ipynb).

