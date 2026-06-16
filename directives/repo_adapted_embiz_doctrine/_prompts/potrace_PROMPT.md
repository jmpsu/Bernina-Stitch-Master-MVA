Read this local source bundle and create complete EMBIZ-specific operational doctrine.

Repository: potrace
Local source: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace
Bundle: /root/embroidery_business_agent_system/directives/repo_adapted_embiz_doctrine/_prompts/potrace_SOURCE_BUNDLE.md

EMBIZ context:
- Root: /root/embroidery_business_agent_system
- Local corpus: /root/web-archive/ai_agents_skills_library
- OpenClaw: /root/.openclaw/workspace
- Agent bus: /usr/local/bin/agent-msg
- Slack mirror outbound-only; no secrets.
- Human approval required before customer contact.
- Human approval required before digitizing.
- Never claim SVG/PES/DST/EXP/INF/BMP exists unless file exists on disk.
- Named agents: Maya, Madeline, Morgan, Mila, Melanie, Mackenzie, Marina, Monica, Meredith, Mckenna, Margaret, Miranda, Michaela, Maeve, Matilda, Melody, Miriam, Mallory

You must adapt this repo into EMBIZ doctrine, not summarize it.

Write these sections:
# potrace EMBIZ ADAPTED DOCTRINE
## Source Material Read
## What This Repo Contributes To EMBIZ
## EMBIZ-Specific Adaptation
## Assigned Agent Ownership
## Local Skill / Knowledge Library Integration
## Runtime Rules
## Required Files / Configs
## Commands / Checks
## Security Restrictions
## Verification Checklist
## Build Tasks
## What Not To Use
## Integration Status

Now use this source bundle:


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/check/checkbin.c =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */

/* Check whether a text file uses CR or CRLF style line endings, by
   checking the first line only. Return 1 if the first line ends in CR
   or CRLF, and 0 otherwise. Return 2 on error. */

#include <stdio.h>
#include <string.h>
#include <errno.h>

#include "../src/platform.h"

int checkbin(FILE *f) {
  int c;

  while (1) {
    c = fgetc(f);
    if (c == EOF) {
      return 0;
    } else if (c == '\n') {
      return 0;
    } else if (c == '\r') {
      return 1;
    }
  }
}

int main(int ac, char **av) {
  char *file;
  FILE *f;
  int r;

  platform_init();

  if (ac != 2) {
    fprintf(stderr, "checkbin: wrong number of arguments\n");
    fprintf(stderr, "Usage: checkbin file\n");
    return 2;
  }

  file = av[1];
  if (strcmp(file, "-") == 0) {
    f = stdin;
  } else {
    f = fopen(file, "rb");
    if (!f) {
      fprintf(stderr, "checkbin: %s: %s\n", file, strerror(errno));
      return 2;
    }
  }
  r = checkbin(f);
  if (strcmp(file, "-") == 0) {
    /* nothing */
  } else {
    fclose(f);
  }
  return r;
}
  


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/check/pgmdiff.c =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */


/* This program compares two equal sized PGM files and outputs a
   numerical difference, which is proportional to the sum of the
   squares of all pixel differences. Return value is 0 on success, 1
   if the pixmaps were different sizes, or 2 on other error. */

#include <stdio.h>
#include <string.h>
#include <errno.h>

#include "../src/greymap.h"
#include "../src/platform.h"

int main(int ac, char **av) {
  char *file1, *file2;
  FILE *f;
  greymap_t *g1, *g2;
  int r;
  double diff;
  int x, y, d;

  platform_init();

  if (ac != 3) {
    fprintf(stderr, "pgmdiff: wrong number of arguments\n");
    fprintf(stderr, "Usage: pgmdiff file1 file2\n");
    return 2;
  }

  file1 = av[1];
  file2 = av[2];

  /* read the greymaps */

  if (strcmp(file1, "-")==0) {
    r = gm_read(stdin, &g1);
  } else {
    f = fopen(file1, "rb");
    if (!f) {
      fprintf(stderr, "pgmdiff: %s: %s\n", file1, strerror(errno));
      return 2;
    }
    r = gm_read(f, &g1);
    fclose(f);
  }
  if (r==-1) {
    fprintf(stderr, "pgmdiff: %s: %s\n", file1, strerror(errno));
    return 2;
  } else if (r) {
    fprintf(stderr, "pgmdiff: %s: bad pgm file\n", file1);
    return 2;
  }

  if (strcmp(file2, "-")==0) {
    r = gm_read(stdin, &g2);
  } else {
    f = fopen(file2, "rb");
    if (!f) {
      fprintf(stderr, "pgmdiff: %s: %s\n", file2, strerror(errno));
      return 2;
    }
    r = gm_read(f, &g2);
    fclose(f);
  }
  if (r==-1) {
    fprintf(stderr, "pgmdiff: %s: %s\n", file2, strerror(errno));
    return 2;
  } else if (r) {
    fprintf(stderr, "pgmdiff: %s: bad pgm file\n", file2);
    return 2;
  }

  if (g1->h != g2->h || g1->w != g2->w) {
    fprintf(stderr, "pgmdiff: images have differing dimensions\n");
    return 1;
  }

  /* compare them */
  diff = 0;

  for (y=0; y<g1->h; y++) {
    for (x=0; x<g1->w; x++) {
      d = GM_UGET(g1, x, y) - GM_UGET(g2, x, y);
      if (d) {
	diff += d*d;
      }
    }
  }

  /* normalize */
  diff /= g1->h * g1->w;
  
  printf("%ld\n", (long)diff);

  gm_free(g1);
  gm_free(g2);
  return 0;
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/doc/dictionary.txt =====

alphamax
antialiasing
API
backend
backends
Bezier
bitonal
blacklevel
BMP
bottommargin
ca
cartesian
cleartext
CNC
despeckle
Despeckling
dpi
dxf
endian
eps
fB
fBmkbitmap
fBpotrace
fi
fI
fIangle
fIdim
fIfilename
fIformat
fillcolor
fImode
fIn
fIname
fIoptions
fIpolicy
fP
fPx
frontend
GeoJSON
geojson
Gimp
gimppath
greymap
greymaps
greyscale
http
jaggy
leftmargin
longcoding
longcurve
min
nf
opticurve
opttolerance
org
pagesize
param
parentless
PBM
pdf
pdfpage
PDFPage
pgm
pnm
PostScript
potrace
Potrace's
potracelib
PPM
ps
pt
rasterizes
rightmargin
rrggbb
scanline
scanlines
selinger
sourceforge
SS
svg
topmargin
TP
turdsize
turnpolicies
turnpolicy
vt
www
XFig
xfig
zlib


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/auxiliary.h =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */

/* This header file collects some general-purpose macros (and static
   inline functions) that are used in various places. */

#ifndef AUXILIARY_H
#define AUXILIARY_H

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdlib.h>

/* ---------------------------------------------------------------------- */
/* point arithmetic */

#include "potracelib.h"

struct point_s {
  long x;
  long y;
};
typedef struct point_s point_t;

typedef potrace_dpoint_t dpoint_t;

/* convert point_t to dpoint_t */
static inline dpoint_t dpoint(point_t p) {
  dpoint_t res;
  res.x = p.x;
  res.y = p.y;
  return res;
}

/* range over the straight line segment [a,b] when lambda ranges over [0,1] */
static inline dpoint_t interval(double lambda, dpoint_t a, dpoint_t b) {
  dpoint_t res;

  res.x = a.x + lambda * (b.x - a.x);
  res.y = a.y + lambda * (b.y - a.y);
  return res;
}

/* ---------------------------------------------------------------------- */
/* some useful macros. Note: the "mod" macro works correctly for
   negative a. Also note that the test for a>=n, while redundant,
   speeds up the mod function by 70% in the average case (significant
   since the program spends about 16% of its time here - or 40%
   without the test). The "floordiv" macro returns the largest integer
   <= a/n, and again this works correctly for negative a, as long as
   a,n are integers and n>0. */

/* integer arithmetic */

static inline int mod(int a, int n) {
  return a>=n ? a%n : a>=0 ? a : n-1-(-1-a)%n;
}

static inline int floordiv(int a, int n) {
  return a>=0 ? a/n : -1-(-1-a)/n;
}

/* Note: the following work for integers and other numeric types. */
#undef sign
#undef abs
#undef min
#undef max
#undef sq
#undef cu
#define sign(x) ((x)>0 ? 1 : (x)<0 ? -1 : 0)
#define abs(a) ((a)>0 ? (a) : -(a))
#define min(a,b) ((a)<(b) ? (a) : (b))
#define max(a,b) ((a)>(b) ? (a) : (b))
#define sq(a) ((a)*(a))
#define cu(a) ((a)*(a)*(a))

#endif /* AUXILIARY_H */


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/backend_dxf.c =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */

/* The DXF backend of Potrace. */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <math.h>

#include "main.h"
#include "backend_dxf.h"
#include "potracelib.h"
#include "lists.h"
#include "auxiliary.h"
#include "trans.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/* ---------------------------------------------------------------------- */
/* auxiliary linear algebra functions */

/* subtract two vectors */
static dpoint_t sub(dpoint_t v, dpoint_t w) {
  dpoint_t r;

  r.x = v.x - w.x;
  r.y = v.y - w.y;
  return r;
}

/* inner product */
static double iprod(dpoint_t v, dpoint_t w) {
  return v.x * w.x + v.y * w.y;
}

/* cross product */
static double xprod(dpoint_t v, dpoint_t w) {
  return v.x * w.y - v.y * w.x;
}

/* calculate the DXF polyline "bulge" value corresponding to the angle
   between two vectors. In case of "infinity" return 0.0. */
static double bulge(dpoint_t v, dpoint_t w) {
  double v2, w2, vw, vxw, nvw;

  v2 = iprod(v, v);
  w2 = iprod(w, w);
  vw = iprod(v, w);
  vxw = xprod(v, w);
  nvw = sqrt(v2 * w2);

  if (vxw == 0.0) {
    return 0.0;
  }    

  return (nvw - vw) / vxw;
}

/* ---------------------------------------------------------------------- */
/* DXF output synthesis */

/* print with group code: the low-level DXF file format */
static int ship(FILE *fout, int gc, const char *fmt, ...) {
  va_list args;
  int r;
  int c;

  r = fprintf(fout, "%3d\n", gc);
  if (r < 0) {
    return r;
  }
  c = r;
  va_start(args, fmt);
  r = vfprintf(fout, fmt, args);
  va_end(args);
  if (r < 0) {
    return r;
  }
  c += r;
  r = fprintf(fout, "\n");
  if (r < 0) {
    return r;
  }
  c += r;
  return c;
}

/* output the start of a polyline */
static void ship_polyline(FILE *fout, const char *layer, int closed) {
  ship(fout, 0, "POLYLINE");
  ship(fout, 8, "%s", layer);
  ship(fout, 66, "%d", 1);
  ship(fout, 70, "%d", closed ? 1 : 0);
}

/* output a vertex */
static void ship_vertex(FILE *fout, const char *layer, dpoint_t v, double bulge) {
  ship(fout, 0, "VERTEX");
  ship(fout, 8, "%s", layer);
  ship(fout, 10, "%f", v.x);
  ship(fout, 20, "%f", v.y);
  ship(fout, 42, "%f", bulge);
}

/* output the end of a polyline */
static void ship_seqend(FILE *fout) {
  ship(fout, 0, "SEQEND");
}

/* output a comment */
static void ship_comment(FILE *fout, const char *comment) {
  ship(fout, 999, "%s", comment);
}

/* output the start of a section */
static void ship_section(FILE *fout, const char *name) {
  ship(fout, 0, "SECTION");
  ship(fout, 2, "%s", name);
}

static void ship_endsec(FILE *fout) {
  ship(fout, 0, "ENDSEC");
}

static void ship_eof(FILE *fout) {
  ship(fout, 0, "EOF");
}

/* ---------------------------------------------------------------------- */
/* Simulated quadratic and bezier curves */

/* Output vertices (with bulges) corresponding to a smooth pair of
   circular arcs from A to B, tangent to AC at A and to CB at
   B. Segments are meant to be concatenated, so don't output the final
   vertex. */
static void pseudo_quad(FILE *fout, const char *layer, dpoint_t A, dpoint_t C, dpoint_t B) {
  dpoint_t v, w;
  double v2, w2, vw, vxw, nvw;
  double a, b, c, y;
  dpoint_t G;
  double bulge1, bulge2;

  v = sub(A, C);
  w = sub(B, C);

  v2 = iprod(v, v);
  w2 = iprod(w, w);
  vw = iprod(v, w);
  vxw = xprod(v, w);
  nvw = sqrt(v2 * w2);

  a = v2 + 2*vw + w2;
  b = v2 + 2*nvw + w2;
  c = 4*nvw;
  if (vxw == 0 || a == 0) {
    goto degenerate;
  }
  /* assert: a,b,c >= 0, b*b - a*c >= 0, and 0 <= b - sqrt(b*b - a*c) <= a */
  y = (b - sqrt(b*b - a*c)) / a;
  G = interval(y, C, interval(0.5, A, B));

  bulge1 = bulge(sub(A,G), v);
  bulge2 = bulge(w, sub(B,G));

  ship_vertex(fout, layer, A, -bulge1);
  ship_vertex(fout, layer, G, -bulge2);
  return;

 degenerate:
  ship_vertex(fout, layer, A, 0);

  return;


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/backend_dxf.h =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */


#ifndef BACKEND_DXF_H
#define BACKEND_DXF_H

#include "potracelib.h"
#include "main.h"

int page_dxf(FILE *fout, potrace_path_t *plist, imginfo_t *imginfo);

#endif /* BACKEND_DXF_H */



===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/backend_eps.c =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */


/* The Postscript backend of Potrace. This can produce "ps" or "eps"
   output, and different kinds of graphical debugging
   output. Postscript compression is optionally supplied via the
   functions in flate.c. */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

#include "potracelib.h"
#include "curve.h"
#include "main.h"
#include "backend_eps.h"
#include "flate.h"
#include "lists.h"
#include "auxiliary.h"

#define SAFE_CALLOC(var, n, typ) \
  if ((var = (typ *)calloc(n, sizeof(typ))) == NULL) goto calloc_error 

typedef int color_t;

#define black  0x000000
#define red    0xff0000
#define green  0x008000
#define blue   0x0000ff

#define TRY(x) if (x) goto try_error

/* ---------------------------------------------------------------------- */
/* functions for interfacing with compression backend */

/* xship: callback function that must be initialized before calling
   any other functions of the "ship" family. xship_file must be
   initialized too. */

/* print the token to f, but filtered through a compression
   filter in case filter!=0 */
static int (*xship)(FILE *f, int filter, const char *s, int len);
static FILE *xship_file;

/* ship postscript code, filtered */
static int ship(const char *fmt, ...) {
  va_list args;
  static char buf[4096]; /* static string limit is okay here because
			    we only use constant format strings - for
			    the same reason, it is okay to use
			    vsprintf instead of vsnprintf below. */
  va_start(args, fmt);
  vsprintf(buf, fmt, args);
  buf[4095] = 0;
  va_end(args);

  xship(xship_file, 1, buf, strlen(buf));
  return 0;
}  

/* ship a postscript comment, unfiltered */
static int shipcom(const char *fmt, ...) {
  static char buf[4096];
  va_list args;

  va_start(args, fmt);
  vsprintf(buf, fmt, args);
  buf[4095] = 0;
  va_end(args);

  xship(xship_file, 0, buf, strlen(buf));
  return 0;
}

/* set all callback functions */
static void eps_callbacks(FILE *fout) {
  if (info.compress && info.pslevel==2) {
    xship = lzw_xship;
  } else if (info.compress && info.pslevel==3) {
    xship = flate_xship;
  } else {
    xship = dummy_xship;
  }
  xship_file = fout;
}  

/* ---------------------------------------------------------------------- */
/* postscript path-drawing auxiliary functions */

/* coordinate quantization */
static inline point_t unit(dpoint_t p) {
  point_t q;

  q.x = (long)(floor(p.x*info.unit+.5));
  q.y = (long)(floor(p.y*info.unit+.5));
  return q;
}

/* current point */
static point_t cur;

static void eps_coords(dpoint_t p) {
  cur = unit(p);
  ship("%ld %ld ", cur.x, cur.y);
}

static void eps_rcoords(dpoint_t p) {
  point_t q;

  q = unit(p);
  ship("%ld %ld ", q.x-cur.x, q.y-cur.y);
  cur = q;
}

static void eps_moveto(dpoint_t p) {
  eps_coords(p);
  ship("moveto\n");
}

/* move to point + offset */
static void eps_moveto_offs(dpoint_t p, double xoffs, double yoffs) {
  /* note: structs are passed by value, so the following assignment
     does not modify the original struct in the caller */
  p.x += xoffs;
  p.y += yoffs;
  eps_coords(p);
  ship("moveto\n");
}

static void eps_lineto(dpoint_t p) {
  eps_rcoords(p);
  ship("rlineto\n");
}

static void eps_curveto(dpoint_t p1, dpoint_t p2, dpoint_t p3) {
  point_t q1, q2, q3;

  q1 = unit(p1);
  q2 = unit(p2);
  q3 = unit(p3);

  ship("%ld %ld %ld %ld %ld %ld rcurveto\n", q1.x-cur.x, q1.y-cur.y, q2.x-cur.x, q2.y-cur.y, q3.x-cur.x, q3.y-cur.y);
  
  cur = q3;
}

/* this procedure returns a statically allocated string */
static const char *eps_colorstring(const color_t col) {
  double r, g, b;
  static char buf[100];

  r = (col & 0xff0000) >> 16;
  g = (col & 0x00ff00) >> 8;
  b = (col & 0x0000ff) >> 0;

  if (r==0 && g==0 && b==0) {
    return "0 setgray";
  } else if (r==255 && g==255 && b==255) {
    return "1 setgray";
  } else if (r == g && g == b) {
    sprintf(buf, "%.3f setgray", r/255.0);
    return buf;
  } else {
    sprintf(buf, "%.3f %.3f %.3f setrgbcolor", r/255.0, g/255.0, b/255.0);
    return buf;
  }
}

static color_t eps_color = -1;
static double eps_width = -1;

static void eps_setcolor(const color_t col) {


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/backend_eps.h =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */


#ifndef BACKEND_EPS_H
#define BACKEND_EPS_H

#include "potracelib.h"
#include "main.h"

int init_ps(FILE *fout);
int page_ps(FILE *fout, potrace_path_t *plist, imginfo_t *imginfo);
int term_ps(FILE *fout);

int page_eps(FILE *fout, potrace_path_t *plist, imginfo_t *imginfo);

#endif /* BACKEND_EPS_H */



===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/backend_geojson.c =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */

/* The GeoJSON backend of Potrace. */
/* Written 2012 by Christoph Hormann <chris_hormann@gmx.de> */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <math.h>

#include "potracelib.h"
#include "curve.h"
#include "main.h"
#include "backend_geojson.h"
#include "lists.h"
#include "auxiliary.h"

/* ---------------------------------------------------------------------- */
/* auxiliary */

/* return a point on a 1-dimensional Bezier segment */
static inline double bezier(double t, double x0, double x1, double x2, double x3) {
  double s = 1-t;
  return s*s*s*x0 + 3*(s*s*t)*x1 + 3*(t*t*s)*x2 + t*t*t*x3;
}

static const char *format = "%f";

/* Convert a floating-point number to a string, using a pre-determined
   format. The format must be previously set with set_format().
   Returns one of a small number of statically allocated strings. */
static char *round_to_unit(double x) {
  static int n = 0;
  static char buf[4][100];

  n++;
  if (n >= 4) {
    n = 0;
  }
  sprintf(buf[n], format, x);
  return buf[n];
}

/* Select a print format for floating point numbers, appropriate for
   the given scaling and info.unit. Note: the format must be so that
   the resulting number fits into a buffer of size 100. */
static void set_format(trans_t tr) {
  double s;
  int d;
  static char buf[10];

  s = min(fabs(tr.scalex), fabs(tr.scaley));
  if (info.unit != 0.0 && s != 0.0) {
    d = (int)ceil(log(info.unit/s) / log(10));
  } else {
    d = 0;
  }
  if (d <= 0) {
    format = "%.0f";
  } else if (d <= 20) {
    sprintf(buf, "%%.%df", d);
    format = buf;
  } else {
    format = "%e";
  }  
}

/* ---------------------------------------------------------------------- */
/* path-drawing auxiliary functions */

static dpoint_t cur;

static void geojson_moveto(FILE *fout, dpoint_t p, trans_t tr) {
  dpoint_t q;

  q = trans(p, tr);

  fprintf(fout, "[%s, %s]", round_to_unit(q.x), round_to_unit(q.y));

  cur = q;
}

static void geojson_lineto(FILE *fout, dpoint_t p, trans_t tr) {
  dpoint_t q;

  q = trans(p, tr);

  fprintf(fout, ", [%s, %s]", round_to_unit(q.x), round_to_unit(q.y));

  cur = q;
}

static void geojson_curveto(FILE *fout, dpoint_t p1, dpoint_t p2, dpoint_t p3, trans_t tr) {
  dpoint_t q1;
  dpoint_t q2;
  dpoint_t q3;
  double step, t;
  int i;
  double x, y;

  q1 = trans(p1, tr);
  q2 = trans(p2, tr);
  q3 = trans(p3, tr);

  step = 1.0 / 8.0;

  for (i=0, t=step; i<8; i++, t+=step) {
    x = bezier(t, cur.x, q1.x, q2.x, q3.x);
    y = bezier(t, cur.y, q1.y, q2.y, q3.y);

    fprintf(fout, ", [%s, %s]", round_to_unit(x), round_to_unit(y));
  }

  cur = q3;
}

/* ---------------------------------------------------------------------- */
/* functions for converting a path to an SVG path element */

static int geojson_path(FILE *fout, potrace_curve_t *curve, trans_t tr) {
  int i;
  dpoint_t *c;
  int m = curve->n;

  fprintf(fout, "      [");

  c = curve->c[m-1];
  geojson_moveto(fout, c[2], tr);

  for (i=0; i<m; i++) {
    c = curve->c[i];
    switch (curve->tag[i]) {
    case POTRACE_CORNER:
      geojson_lineto(fout, c[1], tr);
      geojson_lineto(fout, c[2], tr);
      break;
    case POTRACE_CURVETO:
      geojson_curveto(fout, c[0], c[1], c[2], tr);
      break;
    }
  }

  fprintf(fout, " ]");

  return 0;
}


static void write_polygons(FILE *fout, potrace_path_t *tree, trans_t tr, int first) {
  potrace_path_t *p, *q;

  for (p=tree; p; p=p->sibling) {

    if (!first) fprintf(fout, ",\n");

    fprintf(fout, "{ \"type\": \"Feature\",\n");
    fprintf(fout, "  \"properties\": { },\n");
    fprintf(fout, "  \"geometry\": {\n");
    fprintf(fout, "    \"type\": \"Polygon\",\n");
    fprintf(fout, "    \"coordinates\": [\n");

    geojson_path(fout, &p->curve, tr);

    for (q=p->childlist; q; q=q->sibling) {
      fprintf(fout, ",\n");
      geojson_path(fout, &q->curve, tr);
    }

    fprintf(fout, "    ]\n");
    fprintf(fout, "  }\n");
    fprintf(fout, "}");

    for (q=p->childlist; q; q=q->sibling) {
      write_polygons(fout, q->childlist, tr, 0);


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/backend_geojson.h =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */


#ifndef BACKEND_GEO_H
#define BACKEND_GEO_H

#include "potracelib.h"
#include "main.h"

int page_geojson(FILE *fout, potrace_path_t *plist, imginfo_t *imginfo);

#endif /* BACKEND_GEO_H */



===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/backend_pdf.c =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */


/* The PDF backend of Potrace. Stream compression is optionally
	supplied via the functions in flate.c. */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

#include "main.h"
#include "backend_pdf.h"
#include "flate.h"
#include "lists.h"
#include "potracelib.h"
#include "auxiliary.h"

typedef int color_t;

#define TRY(x) if (x) goto try_error

/* ---------------------------------------------------------------------- */
/* auxiliary: growing arrays */

struct intarray_s {
  int size;
  int *data;
};
typedef struct intarray_s intarray_t;

static inline void intarray_init(intarray_t *ar) {
  ar->size = 0;
  ar->data = NULL;
}

static inline void intarray_term(intarray_t *ar) {
  free(ar->data);
  ar->size = 0;
  ar->data = NULL;
}

/* Set ar[n]=val. Expects n>=0. Grows array if necessary. Return 0 on
   success and -1 on error with errno set. */
static inline int intarray_set(intarray_t *ar, int n, int val) {
  int *p;
  int s;

  if (n >= ar->size) {
    s = n+1024;
    p = (int *)realloc(ar->data, s * sizeof(int));
    if (!p) {
      return -1;
    }
    ar->data = p;
    ar->size = s;
  }
  ar->data[n] = val;
  return 0;
}

/* ---------------------------------------------------------------------- */
/* some global variables */

static intarray_t xref;
static int nxref = 0;
static intarray_t pages;
static int npages;
static int streamofs;
static size_t outcount;  /* output file position */

/* ---------------------------------------------------------------------- */
/* functions for interfacing with compression backend */

/* xship: callback function that must be initialized before calling
   any other functions of the "ship" family. xship_file must be
   initialized too. */

/* print the token to f, but filtered through a compression
   filter in case filter!=0 */
static int (*xship)(FILE *f, int filter, const char *s, int len);
static FILE *xship_file;

/* ship PDF code, filtered */
static int ship(const char *fmt, ...) {
  va_list args;
  static char buf[4096]; /* static string limit is okay here because
			    we only use constant format strings - for
			    the same reason, it is okay to use
			    vsprintf instead of vsnprintf below. */
  va_start(args, fmt);
  vsprintf(buf, fmt, args);
  buf[4095] = 0;
  va_end(args);

  outcount += xship(xship_file, 1, buf, strlen(buf));
  return 0;
}  

/* ship PDF code, unfiltered */
static int shipclear(const char *fmt, ...) {
  static char buf[4096];
  va_list args;

  va_start(args, fmt);
  vsprintf(buf, fmt, args);
  buf[4095] = 0;
  va_end(args);

  outcount += xship(xship_file, 0, buf, strlen(buf));
  return 0;
}

/* set all callback functions */
static void pdf_callbacks(FILE *fout) {

  if (info.compress) {
    xship = pdf_xship;
  } else {
    xship = dummy_xship;
  }
  xship_file = fout;
}  

/* ---------------------------------------------------------------------- */
/* PDF path-drawing auxiliary functions */

/* coordinate quantization */
static inline point_t unit(dpoint_t p) {
  point_t q;

  q.x = (long)(floor(p.x*info.unit+.5));
  q.y = (long)(floor(p.y*info.unit+.5));
  return q;
}

static void pdf_coords(dpoint_t p) {
  point_t cur = unit(p);
  ship("%ld %ld ", cur.x, cur.y);
}

static void pdf_moveto(dpoint_t p) {
  pdf_coords(p);
  ship("m\n");
}

static void pdf_lineto(dpoint_t p) {
  pdf_coords(p);
  ship("l\n");
}

static void pdf_curveto(dpoint_t p1, dpoint_t p2, dpoint_t p3) {
  point_t q1, q2, q3;

  q1 = unit(p1);
  q2 = unit(p2);
  q3 = unit(p3);

  ship("%ld %ld %ld %ld %ld %ld c\n", q1.x, q1.y, q2.x, q2.y, q3.x, q3.y);
}

/* this procedure returns a statically allocated string */
static const char *pdf_colorstring(const color_t col) {
  double r, g, b;
  static char buf[100];

  r = (col & 0xff0000) >> 16;
  g = (col & 0x00ff00) >> 8;
  b = (col & 0x0000ff) >> 0;

  if (r==0 && g==0 && b==0) {
    return "0 g";
  } else if (r==255 && g==255 && b==255) {


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/backend_pdf.h =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */


#ifndef BACKEND_PDF_H
#define BACKEND_PDF_H

#include "potracelib.h"
#include "main.h"

int init_pdf(FILE *fout);
int page_pdf(FILE *fout, potrace_path_t *plist, imginfo_t *imginfo);
int term_pdf(FILE *fout);

int page_pdf(FILE *fout, potrace_path_t *plist, imginfo_t *imginfo);
int page_pdfpage(FILE *fout, potrace_path_t *plist, imginfo_t *imginfo);

#endif /* BACKEND_PDF_H */



===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/backend_pgm.c =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */


/* The PGM backend of Potrace. Here we custom-render a set of Bezier
   curves and output the result as a greymap. This is merely a
   convenience, as the same could be achieved by piping the EPS output
   through ghostscript. */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <math.h>

#include "backend_pgm.h"
#include "potracelib.h"
#include "lists.h"
#include "greymap.h"
#include "render.h"
#include "main.h"
#include "auxiliary.h"
#include "trans.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

static void pgm_path(potrace_curve_t *curve, trans_t t, render_t *rm) {
  dpoint_t *c, c1[3];
  int i;
  int m = curve->n;
  
  c = curve->c[m-1];
  c1[2] = trans(c[2], t);
  render_moveto(rm, c1[2].x, c1[2].y);
  
  for (i=0; i<m; i++) {
    c = curve->c[i];
    switch (curve->tag[i]) {
    case POTRACE_CORNER:
      c1[1] = trans(c[1], t);
      c1[2] = trans(c[2], t);
      render_lineto(rm, c1[1].x, c1[1].y);
      render_lineto(rm, c1[2].x, c1[2].y);
      break;
    case POTRACE_CURVETO:
      c1[0] = trans(c[0], t);
      c1[1] = trans(c[1], t);
      c1[2] = trans(c[2], t);
      render_curveto(rm, c1[0].x, c1[0].y, c1[1].x, c1[1].y, c1[2].x, c1[2].y);
      break;
    }
  }
}

int page_pgm(FILE *fout, potrace_path_t *plist, imginfo_t *imginfo) {
  potrace_path_t *p;
  greymap_t *gm;
  render_t *rm;
  int w, h;
  trans_t t;
  int mode;
  const char *comment = "created by " POTRACE " " VERSION ", written by Peter Selinger 2001-2019";

  t.bb[0] = imginfo->trans.bb[0]+imginfo->lmar+imginfo->rmar;
  t.bb[1] = imginfo->trans.bb[1]+imginfo->tmar+imginfo->bmar;
  t.orig[0] = imginfo->trans.orig[0]+imginfo->lmar;
  t.orig[1] = imginfo->trans.orig[1]+imginfo->bmar;
  t.x[0] = imginfo->trans.x[0];
  t.x[1] = imginfo->trans.x[1];
  t.y[0] = imginfo->trans.y[0];
  t.y[1] = imginfo->trans.y[1];

  w = (int)ceil(t.bb[0]);
  h = (int)ceil(t.bb[1]);

  gm = gm_new(w, h);
  if (!gm) {
    return 1;
  }
  rm = render_new(gm);
  if (!rm) {
    return 1;
  }

  gm_clear(gm, 255); /* white */

  list_forall(p, plist) {
    pgm_path(&p->curve, t, rm);
  }

  render_close(rm);

  /* if negative orientation, make sure to invert effect of rendering */
  mode = imginfo->width * imginfo->height < 0 ? GM_MODE_NEGATIVE : GM_MODE_POSITIVE;

  gm_writepgm(fout, rm->gm, comment, 1, mode, info.gamma);

  render_free(rm);
  gm_free(gm);

  return 0;
}



===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/backend_pgm.h =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */


#ifndef BACKEND_PGM_H
#define BACKEND_PGM_H

#include <stdio.h>

#include "potracelib.h"
#include "main.h"

int page_pgm(FILE *fout, potrace_path_t *plist, imginfo_t *imginfo);

#endif /* BACKEND_PGM_H */


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/backend_svg.c =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */


/* The SVG backend of Potrace. */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <math.h>

#include "potracelib.h"
#include "curve.h"
#include "main.h"
#include "backend_svg.h"
#include "lists.h"
#include "auxiliary.h"

/* ---------------------------------------------------------------------- */
/* path-drawing auxiliary functions */

/* coordinate quantization */
static inline point_t unit(dpoint_t p) {
  point_t q;

  q.x = (long)(floor(p.x*info.unit+.5));
  q.y = (long)(floor(p.y*info.unit+.5));
  return q;
}

static point_t cur;
static char lastop = 0;
static int column = 0;
static int newline = 1;

static void shiptoken(FILE *fout, const char *token) {
  int c = strlen(token);
  if (!newline && column+c+1 > 75) {
    fprintf(fout, "\n");
    column = 0;
    newline = 1;
  } else if (!newline) {
    fprintf(fout, " ");
    column++;
  }
  fprintf(fout, "%s", token);
  column += c;
  newline = 0;
}

static void ship(FILE *fout, const char *fmt, ...) {
  va_list args;
  static char buf[4096]; /* static string limit is okay here because
			    we only use constant format strings - for
			    the same reason, it is okay to use
			    vsprintf instead of vsnprintf below. */
  char *p, *q;

  va_start(args, fmt);
  vsprintf(buf, fmt, args);
  buf[4095] = 0;
  va_end(args);

  p = buf;
  while ((q = strchr(p, ' ')) != NULL) {
    *q = 0;
    shiptoken(fout, p);
    p = q+1;
  }
  shiptoken(fout, p);
}

static void svg_moveto(FILE *fout, dpoint_t p) {
  cur = unit(p);

  ship(fout, "M%ld %ld", cur.x, cur.y);
  lastop = 'M';
}

static void svg_rmoveto(FILE *fout, dpoint_t p) {
  point_t q;

  q = unit(p);
  ship(fout, "m%ld %ld", q.x-cur.x, q.y-cur.y);
  cur = q;
  lastop = 'm';
}

static void svg_lineto(FILE *fout, dpoint_t p) {
  point_t q;

  q = unit(p);

  if (lastop != 'l') {
    ship(fout, "l%ld %ld", q.x-cur.x, q.y-cur.y);
  } else {
    ship(fout, "%ld %ld", q.x-cur.x, q.y-cur.y);
  }
  cur = q;
  lastop = 'l';
}

static void svg_curveto(FILE *fout, dpoint_t p1, dpoint_t p2, dpoint_t p3) {
  point_t q1, q2, q3;

  q1 = unit(p1);
  q2 = unit(p2);
  q3 = unit(p3);

  if (lastop != 'c') {
    ship(fout, "c%ld %ld %ld %ld %ld %ld", q1.x-cur.x, q1.y-cur.y, q2.x-cur.x, q2.y-cur.y, q3.x-cur.x, q3.y-cur.y);
  } else {
    ship(fout, "%ld %ld %ld %ld %ld %ld", q1.x-cur.x, q1.y-cur.y, q2.x-cur.x, q2.y-cur.y, q3.x-cur.x, q3.y-cur.y);
  }
  cur = q3;
  lastop = 'c';
}

/* ---------------------------------------------------------------------- */
/* functions for converting a path to an SVG path element */

/* Explicit encoding. If abs is set, move to first coordinate
   absolutely. */
static int svg_path(FILE *fout, potrace_curve_t *curve, int abs) {
  int i;
  dpoint_t *c;
  int m = curve->n;

  c = curve->c[m-1];
  if (abs) {
    svg_moveto(fout, c[2]);
  } else {
    svg_rmoveto(fout, c[2]);
  }

  for (i=0; i<m; i++) {
    c = curve->c[i];
    switch (curve->tag[i]) {
    case POTRACE_CORNER:
      svg_lineto(fout, c[1]);
      svg_lineto(fout, c[2]);
      break;
    case POTRACE_CURVETO:
      svg_curveto(fout, c[0], c[1], c[2]);
      break;
    }
  }
  newline = 1;
  shiptoken(fout, "z");
  return 0;
}

/* produce a jaggy path - for debugging. If abs is set, move to first
   coordinate absolutely. If abs is not set, move to first coordinate
   relatively, and traverse path in the opposite direction. */
static int svg_jaggy_path(FILE *fout, point_t *pt, int n, int abs) {
  int i;
  point_t cur, prev;
  
  if (abs) {
    cur = prev = pt[n-1];
    svg_moveto(fout, dpoint(cur));
    for (i=0; i<n; i++) {
      if (pt[i].x != cur.x && pt[i].y != cur.y) {
	cur = prev;
	svg_lineto(fout, dpoint(cur));
      }
      prev = pt[i];
    }
    svg_lineto(fout, dpoint(pt[n-1]));
  } else {
    cur = prev = pt[0];
    svg_rmoveto(fout, dpoint(cur));
    for (i=n-1; i>=0; i--) {
      if (pt[i].x != cur.x && pt[i].y != cur.y) {


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/backend_svg.h =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */


#ifndef BACKEND_SVG_H
#define BACKEND_SVG_H

#include "potracelib.h"
#include "main.h"

int page_svg(FILE *fout, potrace_path_t *plist, imginfo_t *imginfo);
int page_gimp(FILE *fout, potrace_path_t *plist, imginfo_t *imginfo);

#endif /* BACKEND_SVG_H */



===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/backend_xfig.c =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */


/* The xfig backend of Potrace. */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <math.h>

#include "main.h"
#include "backend_xfig.h"
#include "potracelib.h"
#include "lists.h"
#include "auxiliary.h"
#include "trans.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

struct pageformat_s {
  const char *name;
  int w, h;
};
typedef struct pageformat_s pageformat_t;

/* page formats known by xfig, and their dimensions in postscript points */
static pageformat_t pageformat[] = {
  { "A9",        105,  149 },
  { "A8",        149,  211 },
  { "A7",        211,  298 },
  { "A6",        298,  421 },
  { "A5",        421,  595 },
  { "A4",        595,  842 },
  { "A3",        842, 1191 },
  { "A2",       1191, 1685 },
  { "A1",       1685, 2383 },
  { "A0",       2383, 3370 },

  { "B10",        91,  129 },
  { "B9",        129,  182 },
  { "B8",        182,  258 },
  { "B7",        258,  365 },
  { "B6",        365,  516 },
  { "B5",        516,  730 },
  { "B4",        730, 1032 },
  { "B3",       1032, 1460 },
  { "B2",       1460, 2064 },
  { "B1",       2064, 2920 },
  { "B0",       2920, 4127 },

  { "Letter",    612,  792 },
  { "Legal",     612, 1008 },
  { "Tabloid",   792, 1224 },
  { "A",         612,  792 },
  { "B",         792, 1224 },
  { "C",        1224, 1584 },
  { "D",        1584, 2448 },
  { "E",        2448, 3168 },

  { NULL, 0, 0 },
};

/* ---------------------------------------------------------------------- */
/* path-drawing auxiliary functions */

/* coordinate quantization */
static inline point_t unit(dpoint_t p) {
  point_t q;

  q.x = (long)(floor(p.x+.5));
  q.y = (long)(floor(p.y+.5));
  return q;
}

static void xfig_point(FILE *fout, dpoint_t p, trans_t t) {
  point_t q;

  q = unit(trans(p, t));

  fprintf(fout, "%ld %ld\n", q.x, q.y);
}

/* ---------------------------------------------------------------------- */
/* functions for converting a path to a xfig */

/* calculate number of xfig control points in this path */
static int npoints(potrace_curve_t *curve, int m) {
  int i;
  int n=0;

  for (i=0; i<m; i++) {
    switch (curve->tag[i]) {
    case POTRACE_CORNER:
      n += 1;
      break;
    case POTRACE_CURVETO:
      n += 2;
      break;
    }
  }
  return n;
}

/* do one path. */
static void xfig_path(FILE *fout, potrace_curve_t *curve, trans_t t, int sign, int depth) {
  int i;
  dpoint_t *c;
  int m = curve->n;

  fprintf(fout, "3 1 0 0 0 %d %d 0 20 0.000 0 0 0 %d\n", sign=='+' ? 32 : 33, depth, npoints(curve, m));

  for (i=0; i<m; i++) {
    c = curve->c[i];
    switch (curve->tag[i]) {
    case POTRACE_CORNER:
      xfig_point(fout, c[1], t);
      break;
    case POTRACE_CURVETO:
      xfig_point(fout, c[0], t);
      xfig_point(fout, c[1], t);
      break;
    }
  }
  for (i=0; i<m; i++) {
    switch (curve->tag[i]) {
    case POTRACE_CORNER:
      fprintf(fout, "0\n");
      break;
    case POTRACE_CURVETO:
      fprintf(fout, "1 1\n");
      break;
    }
  }
}

/* render a whole tree */
static void xfig_write_paths(FILE *fout, potrace_path_t *plist, trans_t t, int depth) {
  potrace_path_t *p, *q;

  for (p=plist; p; p=p->sibling) {
    xfig_path(fout, &p->curve, t, p->sign, depth);
    for (q=p->childlist; q; q=q->sibling) {
      xfig_path(fout, &q->curve, t, q->sign, depth >= 1 ? depth-1 : 0);
    }
    for (q=p->childlist; q; q=q->sibling) {
      xfig_write_paths(fout, q->childlist, t, depth >= 2 ? depth-2 : 0);
    }
  }
}

/* calculate the depth of a tree. Call with d=0. */
static int xfig_get_depth(potrace_path_t *plist) {
  potrace_path_t *p;
  int max =0;
  int d;

  for (p=plist; p; p=p->sibling) {
    d = xfig_get_depth(p->childlist);
    if (d > max) {
      max = d;
    }
  }
  return max + 1;
}

/* ---------------------------------------------------------------------- */
/* Backend. */

/* public interface for XFIG */
int page_xfig(FILE *fout, potrace_path_t *plist, imginfo_t *imginfo) {
  trans_t t;
  double origx = imginfo->trans.orig[0] + imginfo->lmar;


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/backend_xfig.h =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */


#ifndef BACKEND_XFIG_H
#define BACKEND_XFIG_H

#include "potracelib.h"
#include "main.h"

int page_xfig(FILE *fout, potrace_path_t *plist, imginfo_t *imginfo);

#endif /* BACKEND_XFIG_H */



===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/bbox.c =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */

/* figure out the true bounding box of a vector image */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <math.h>
#include <stdlib.h>

#include "bbox.h"
#include "potracelib.h"
#include "lists.h"

/* ---------------------------------------------------------------------- */
/* intervals */

/* initialize the interval to [min, max] */
static void interval(interval_t *i, double min, double max) {
  i->min = min;
  i->max = max;
}

/* initialize the interval to [x, x] */
static inline void singleton(interval_t *i, double x) {
  interval(i, x, x);
}

/* extend the interval to include the number x */
static inline void extend(interval_t *i, double x) {
  if (x < i->min) {
    i->min = x;
  } else if (x > i->max) {
    i->max = x;
  }
}

static inline int in_interval(interval_t *i, double x) {
  return i->min <= x && x <= i->max;
}

/* ---------------------------------------------------------------------- */
/* inner product */

typedef potrace_dpoint_t dpoint_t;

static double iprod(dpoint_t a, dpoint_t b) {
  return a.x * b.x + a.y * b.y;
}

/* ---------------------------------------------------------------------- */
/* linear Bezier segments */

/* return a point on a 1-dimensional Bezier segment */
static inline double bezier(double t, double x0, double x1, double x2, double x3) {
  double s = 1-t;
  return s*s*s*x0 + 3*(s*s*t)*x1 + 3*(t*t*s)*x2 + t*t*t*x3;
}

/* Extend the interval i to include the minimum and maximum of a
   1-dimensional Bezier segment given by control points x0..x3. For
   efficiency, x0 in i is assumed as a precondition. */
static void bezier_limits(double x0, double x1, double x2, double x3, interval_t *i) {
  double a, b, c, d, r;
  double t, x;

  /* the min and max of a cubic curve segment are attained at one of
     at most 4 critical points: the 2 endpoints and at most 2 local
     extrema. We don't check the first endpoint, because all our
     curves are cyclic so it's more efficient not to check endpoints
     twice. */

  /* endpoint */
  extend(i, x3);

  /* optimization: don't bother calculating extrema if all control
     points are already in i */
  if (in_interval(i, x1) && in_interval(i, x2)) {
    return;
  }

  /* solve for extrema. at^2 + bt + c = 0 */
  a = -3*x0 + 9*x1 - 9*x2 + 3*x3;
  b = 6*x0 - 12*x1 + 6*x2;
  c = -3*x0 + 3*x1;
  d = b*b - 4*a*c;
  if (d > 0) {
    r = sqrt(d);
    t = (-b-r)/(2*a);
    if (t > 0 && t < 1) {
      x = bezier(t, x0, x1, x2, x3);
      extend(i, x);
    }
    t = (-b+r)/(2*a);
    if (t > 0 && t < 1) {
      x = bezier(t, x0, x1, x2, x3);
      extend(i, x);
    }
  }
  return;
}

/* ---------------------------------------------------------------------- */
/* Potrace segments, curves, and pathlists */

/* extend the interval i to include the inner product <v | dir> for
   all points v on the segment. Assume precondition a in i. */
static inline void segment_limits(int tag, dpoint_t a, dpoint_t c[3], dpoint_t dir, interval_t *i) {
  switch (tag) {
  case POTRACE_CORNER:
    extend(i, iprod(c[1], dir));
    extend(i, iprod(c[2], dir));
    break;
  case POTRACE_CURVETO:
    bezier_limits(iprod(a, dir), iprod(c[0], dir), iprod(c[1], dir), iprod(c[2], dir), i);
    break;
  }
}

/* extend the interval i to include <v | dir> for all points v on the
   curve. */
static void curve_limits(potrace_curve_t *curve, dpoint_t dir, interval_t *i) {
  int k;
  int n = curve->n;

  segment_limits(curve->tag[0], curve->c[n-1][2], curve->c[0], dir, i);
  for (k=1; k<n; k++) {
    segment_limits(curve->tag[k], curve->c[k-1][2], curve->c[k], dir, i);
  }
}

/* compute the interval i to be the smallest interval including all <v
   | dir> for points in the pathlist. If the pathlist is empty, return
   the singleton interval [0,0]. */
void path_limits(potrace_path_t *path, dpoint_t dir, interval_t *i) {
  potrace_path_t *p;

  /* empty image? */
  if (path == NULL) {
    interval(i, 0, 0);
    return;
  }

  /* initialize interval to a point on the first curve */
  singleton(i, iprod(path->curve.c[0][2], dir));

  /* iterate */
  list_forall(p, path) {
    curve_limits(&p->curve, dir, i);
  }
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/bbox.h =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */

#ifndef BBOX_H
#define BBOX_H

#include "potracelib.h"

/* an interval [min, max] */
struct interval_s {
  double min, max;
};
typedef struct interval_s interval_t;

void path_limits(potrace_path_t *path, potrace_dpoint_t dir, interval_t *i);

#endif /* BBOX_H */


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/bitmap.h =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */

#ifndef BITMAP_H
#define BITMAP_H

#include <string.h>
#include <stdlib.h>
#include <errno.h>
#include <stddef.h>

/* The bitmap type is defined in potracelib.h */
#include "potracelib.h"

/* The present file defines some convenient macros and static inline
   functions for accessing bitmaps. Since they only produce inline
   code, they can be conveniently shared by the library and frontends,
   if desired */

/* ---------------------------------------------------------------------- */
/* some measurements */

#define BM_WORDSIZE ((int)sizeof(potrace_word))
#define BM_WORDBITS (8*BM_WORDSIZE)
#define BM_HIBIT (((potrace_word)1)<<(BM_WORDBITS-1))
#define BM_ALLBITS (~(potrace_word)0)

/* macros for accessing pixel at index (x,y). U* macros omit the
   bounds check. */

#define bm_scanline(bm, y) ((bm)->map + (ptrdiff_t)(y)*(ptrdiff_t)(bm)->dy)
#define bm_index(bm, x, y) (&bm_scanline(bm, y)[(x)/BM_WORDBITS])
#define bm_mask(x) (BM_HIBIT >> ((x) & (BM_WORDBITS-1)))
#define bm_range(x, a) ((int)(x) >= 0 && (int)(x) < (a))
#define bm_safe(bm, x, y) (bm_range(x, (bm)->w) && bm_range(y, (bm)->h))
#define BM_UGET(bm, x, y) ((*bm_index(bm, x, y) & bm_mask(x)) != 0)
#define BM_USET(bm, x, y) (*bm_index(bm, x, y) |= bm_mask(x))
#define BM_UCLR(bm, x, y) (*bm_index(bm, x, y) &= ~bm_mask(x))
#define BM_UINV(bm, x, y) (*bm_index(bm, x, y) ^= bm_mask(x))
#define BM_UPUT(bm, x, y, b) ((b) ? BM_USET(bm, x, y) : BM_UCLR(bm, x, y))
#define BM_GET(bm, x, y) (bm_safe(bm, x, y) ? BM_UGET(bm, x, y) : 0)
#define BM_SET(bm, x, y) (bm_safe(bm, x, y) ? BM_USET(bm, x, y) : 0)
#define BM_CLR(bm, x, y) (bm_safe(bm, x, y) ? BM_UCLR(bm, x, y) : 0)
#define BM_INV(bm, x, y) (bm_safe(bm, x, y) ? BM_UINV(bm, x, y) : 0)
#define BM_PUT(bm, x, y, b) (bm_safe(bm, x, y) ? BM_UPUT(bm, x, y, b) : 0)

/* calculate the size, in bytes, required for the data area of a
   bitmap of the given dy and h. Assume h >= 0. Return -1 if the size
   does not fit into the ptrdiff_t type. */
static inline ptrdiff_t getsize(int dy, int h) {
  ptrdiff_t size;

  if (dy < 0) {
    dy = -dy;
  }
  
  size = (ptrdiff_t)dy * (ptrdiff_t)h * (ptrdiff_t)BM_WORDSIZE;

  /* check for overflow error */
  if (size < 0 || (h != 0 && dy != 0 && size / h / dy != BM_WORDSIZE)) {
    return -1;
  }

  return size;
}

/* return the size, in bytes, of the data area of the bitmap. Return
   -1 if the size does not fit into the ptrdiff_t type; however, this
   cannot happen if the bitmap is well-formed, i.e., if created with
   bm_new or bm_dup. */
static inline ptrdiff_t bm_size(const potrace_bitmap_t *bm) {
  return getsize(bm->dy, bm->h);
}

/* calculate the base address of the bitmap data. Assume that the
   bitmap is well-formed, i.e., its size fits into the ptrdiff_t type.
   This is the case if created with bm_new or bm_dup. The base address
   may differ from bm->map if dy is negative */
static inline potrace_word *bm_base(const potrace_bitmap_t *bm) {
  int dy = bm->dy;

  if (dy >= 0 || bm->h == 0) {
    return bm->map;
  } else {
    return bm_scanline(bm, bm->h - 1);
  }  
}

/* free the given bitmap. Leaves errno untouched. */
static inline void bm_free(potrace_bitmap_t *bm) {
  if (bm && bm->map) {
    free(bm_base(bm));
  }
  free(bm);
}

/* return new bitmap initialized to 0. NULL with errno on error.
   Assumes w, h >= 0. */
static inline potrace_bitmap_t *bm_new(int w, int h) {
  potrace_bitmap_t *bm;
  int dy = w == 0 ? 0 : (w - 1) / BM_WORDBITS + 1;
  ptrdiff_t size;

  size = getsize(dy, h);
  if (size < 0) {
    errno = ENOMEM;
    return NULL;
  }
  if (size == 0) {
    size = BM_WORDSIZE; /* make sure calloc() doesn't return NULL */
  } 

  bm = (potrace_bitmap_t *) malloc(sizeof(potrace_bitmap_t));
  if (!bm) {
    return NULL;
  }
  bm->w = w;
  bm->h = h;
  bm->dy = dy;
  bm->map = (potrace_word *) calloc(1, size);
  if (!bm->map) {
    free(bm);
    return NULL;
  }
  return bm;
}

/* clear the given bitmap. Set all bits to c. Assumes a well-formed
   bitmap. */
static inline void bm_clear(potrace_bitmap_t *bm, int c) {
  /* Note: if the bitmap was created with bm_new, then it is
     guaranteed that size will fit into the ptrdiff_t type. */
  ptrdiff_t size = bm_size(bm);
  memset(bm_base(bm), c ? -1 : 0, size);
}

/* duplicate the given bitmap. Return NULL on error with errno
   set. Assumes a well-formed bitmap. */
static inline potrace_bitmap_t *bm_dup(const potrace_bitmap_t *bm) {
  potrace_bitmap_t *bm1 = bm_new(bm->w, bm->h);
  int y;
  
  if (!bm1) {
    return NULL;
  }
  for (y=0; y < bm->h; y++) {
    memcpy(bm_scanline(bm1, y), bm_scanline(bm, y), (size_t)bm1->dy * (size_t)BM_WORDSIZE);
  }
  return bm1;
}

/* invert the given bitmap. */
static inline void bm_invert(potrace_bitmap_t *bm) {
  int dy = bm->dy;
  int y;
  int i;
  potrace_word *p;

  if (dy < 0) {
    dy = -dy;
  }
  
  for (y=0; y < bm->h; y++) {
    p = bm_scanline(bm, y);
    for (i=0; i < dy; i++) {
      p[i] ^= BM_ALLBITS;
    }
  }
}

/* turn the given bitmap upside down. This does not move the bitmap
   data or change the bm_base() address. */
static inline void bm_flip(potrace_bitmap_t *bm) {
  int dy = bm->dy;

  if (bm->h == 0 || bm->h == 1) {
    return;
  }
  


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/bitmap_io.c =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */


/* Routines for manipulating bitmaps, including reading pbm files. */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdio.h>
#ifdef HAVE_INTTYPES_H
#include <inttypes.h>
#endif

#include "bitmap.h"
#include "bitops.h"
#include "bitmap_io.h"

#define INTBITS (8*sizeof(int))

static int bm_readbody_bmp(FILE *f, double threshold, potrace_bitmap_t **bmp);
static int bm_readbody_pnm(FILE *f, double threshold, potrace_bitmap_t **bmp, int magic);

#define TRY(x) if (x) goto try_error
#define TRY_EOF(x) if (x) goto eof
#define TRY_STD(x) if (x) goto std_error

/* ---------------------------------------------------------------------- */
/* routines for reading pnm streams */

/* read next character after whitespace and comments. Return EOF on
   end of file or error. */
static int fgetc_ws(FILE *f) {
  int c;

  while (1) {
    c = fgetc(f);
    if (c=='#') {
      while (1) {
	c = fgetc(f);
	if (c=='\n' || c==EOF) {
	  break;
	}
      }
    }
    /* space, tab, line feed, carriage return, form-feed */
    if (c!=' ' && c!='\t' && c!='\r' && c!='\n' && c!=12) {
      return c;
    }
  }
}

/* skip whitespace and comments, then read a non-negative decimal
   number from a stream. Return -1 on EOF. Tolerate other errors (skip
   bad characters). Do not the read any characters following the
   number (put next character back into the stream) */

static int readnum(FILE *f) {
  int c;
  uint64_t acc;

  /* skip whitespace and comments */
  while (1) {
    c = fgetc_ws(f);
    if (c==EOF) {
      return -1;
    }
    if (c>='0' && c<='9') {
      break;
    }
  }

  /* first digit is already in c */
  acc = c-'0';
  while (1) {
    c = fgetc(f);
    if (c==EOF) {
      break;
    }
    if (c<'0' || c>'9') {
      ungetc(c, f);
      break;
    }
    acc *= 10;
    acc += c-'0';
    if (acc > 0x7fffffff) {
      return -1;
    }
  }
  return acc;
}

/* similar to readnum, but read only a single 0 or 1, and do not read
   any characters after it. */

static int readbit(FILE *f) {
  int c;

  /* skip whitespace and comments */
  while (1) {
    c = fgetc_ws(f);
    if (c==EOF) {
      return -1;
    }
    if (c>='0' && c<='1') {
      break;
    }
  }

  return c-'0';
}

/* ---------------------------------------------------------------------- */

/* read a PNM stream: P1-P6 format (see pnm(5)), or a BMP stream, and
   convert the output to a bitmap. Return bitmap in *bmp. Return 0 on
   success, -1 on error with errno set, -2 on bad file format (with
   error message in bm_read_error), and 1 on premature end of file, -3
   on empty file (including files which contain only whitespace and
   comments), -4 if wrong magic number. If the return value is >=0,
   *bmp is valid. */

const char *bm_read_error = NULL;

int bm_read(FILE *f, double threshold, potrace_bitmap_t **bmp) {
  int magic[2];

  /* read magic number. We ignore whitespace and comments before the
     magic, for the benefit of concatenated files in P1-P3 format.
     Multiple P1-P3 images in a single file are not formally allowed
     by the PNM standard, but there is no harm in being lenient. */

  magic[0] = fgetc_ws(f);
  if (magic[0] == EOF) {
    return -3;
  } 
  magic[1] = fgetc(f);
  if (magic[0] == 'P' && magic[1] >= '1' && magic[1] <= '6') {
    return bm_readbody_pnm(f, threshold, bmp, magic[1]);
  }
  if (magic[0] == 'B' && magic[1] == 'M') {
    return bm_readbody_bmp(f, threshold, bmp);
  }
  return -4;
}

/* ---------------------------------------------------------------------- */
/* read PNM format */

/* read PNM stream after magic number. Return values as for bm_read */
static int bm_readbody_pnm(FILE *f, double threshold, potrace_bitmap_t **bmp, int magic) {
  potrace_bitmap_t *bm;
  int x, y, i, b, b1, sum;
  int bpr; /* bytes per row (as opposed to 4*bm->c) */
  int w, h, max;
  int realheight;  /* in case of incomplete file, keeps track of how
                      many scan lines actually contain data */
  
  bm = NULL;

  w = readnum(f);
  if (w<0) {
    goto format_error;
  }

  h = readnum(f);
  if (h<0) {
    goto format_error;
  }

  /* allocate bitmap */
  bm = bm_new(w, h);
  if (!bm) {
    goto std_error;
  }

  realheight = 0;
  


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/bitmap_io.h =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */

/* bitmap input/output functions */

#ifndef BITMAP_IO_H
#define BITMAP_IO_H

#include <stdio.h>
#include "bitmap.h"

/* Note that bitmaps are stored bottom to top, i.e., the first
   scanline is the bottom-most one */

extern const char *bm_read_error;

int bm_read(FILE *f, double blacklevel, potrace_bitmap_t **bmp);
void bm_writepbm(FILE *f, potrace_bitmap_t *bm);
int bm_print(FILE *f, potrace_bitmap_t *bm);

#endif /* BITMAP_IO_H */



===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/bitops.h =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */


/* bits.h: this file defines some macros for bit manipulations. We
   provide a generic implementation, as well as machine- and
   compiler-specific fast implementations */

/* lobit: return the position of the rightmost "1" bit of an int, or
   32 if none. hibit: return 1 + the position of the leftmost "1" bit
   of an int, or 0 if none. Note: these functions work on 32-bit
   integers. */

#ifndef BITOPS_H
#define BITOPS_H

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

/* ---------------------------------------------------------------------- */
/* machine specific macros */

#if defined(HAVE_I386)

static inline unsigned int lobit(unsigned int x) {
  unsigned int res;
  asm ("bsf	%1,%0\n\t"
       "jnz	0f\n\t"
       "movl	$32,%0\n"
       "0:"
       : "=r" (res)
       : "r" (x)
       : "cc");
  return res;
}

static inline unsigned int hibit(unsigned int x) {
  unsigned int res;					

  asm ("bsr	%1,%0\n\t"
       "jnz	0f\n\t"
       "movl	$-1,%0\n"
       "0:"
       : "=r" (res)
       : "r" (x)
       : "cc");
  return res+1;
}

/* ---------------------------------------------------------------------- */
#else /* generic macros */

static inline unsigned int lobit(unsigned int x) {
  unsigned int res = 32;
  while (x & 0xffffff) {
    x <<= 8;
    res -= 8;
  }
  while (x) {
    x <<= 1;
    res -= 1;
  }
  return res;
}

static inline unsigned int hibit(unsigned int x) {
  unsigned int res = 0;
  while (x > 0xff) {
    x >>= 8;
    res += 8;
  }
  while (x) {
    x >>= 1;
    res += 1;
  }
  return res;
}

#endif 

#endif /* BITOPS_H */


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/curve.c =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */

/* private part of the path and curve data structures */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "potracelib.h"
#include "lists.h"
#include "curve.h"

#define SAFE_CALLOC(var, n, typ) \
  if ((var = (typ *)calloc(n, sizeof(typ))) == NULL) goto calloc_error 

/* ---------------------------------------------------------------------- */
/* allocate and free path objects */

path_t *path_new(void) {
  path_t *p = NULL;
  privpath_t *priv = NULL;

  SAFE_CALLOC(p, 1, path_t);
  memset(p, 0, sizeof(path_t));
  SAFE_CALLOC(priv, 1, privpath_t);
  memset(priv, 0, sizeof(privpath_t));
  p->priv = priv;
  return p;

 calloc_error:
  free(p);
  free(priv);
  return NULL;
}

/* free the members of the given curve structure. Leave errno unchanged. */
static void privcurve_free_members(privcurve_t *curve) {
  free(curve->tag);
  free(curve->c);
  free(curve->vertex);
  free(curve->alpha);
  free(curve->alpha0);
  free(curve->beta);
}

/* free a path. Leave errno untouched. */
void path_free(path_t *p) {
  if (p) {
    if (p->priv) {
      free(p->priv->pt);
      free(p->priv->lon);
      free(p->priv->sums);
      free(p->priv->po);
      privcurve_free_members(&p->priv->curve);
      privcurve_free_members(&p->priv->ocurve);
    }
    free(p->priv);
    /* do not free p->fcurve ! */
  }
  free(p);
}  

/* free a pathlist, leaving errno untouched. */
void pathlist_free(path_t *plist) {
  path_t *p;

  list_forall_unlink(p, plist) {
    path_free(p);
  }
}

/* ---------------------------------------------------------------------- */
/* initialize and finalize curve structures */

typedef dpoint_t dpoint3_t[3];

/* initialize the members of the given curve structure to size m.
   Return 0 on success, 1 on error with errno set. */
int privcurve_init(privcurve_t *curve, int n) {
  memset(curve, 0, sizeof(privcurve_t));
  curve->n = n;
  SAFE_CALLOC(curve->tag, n, int);
  SAFE_CALLOC(curve->c, n, dpoint3_t);
  SAFE_CALLOC(curve->vertex, n, dpoint_t);
  SAFE_CALLOC(curve->alpha, n, double);
  SAFE_CALLOC(curve->alpha0, n, double);
  SAFE_CALLOC(curve->beta, n, double);
  return 0;

 calloc_error:
  free(curve->tag);
  free(curve->c);
  free(curve->vertex);
  free(curve->alpha);
  free(curve->alpha0);
  free(curve->beta);
  return 1;
}

/* copy private to public curve structure */
void privcurve_to_curve(privcurve_t *pc, potrace_curve_t *c) {
  c->n = pc->n;
  c->tag = pc->tag;
  c->c = pc->c;
}
    


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/curve.h =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */

#ifndef CURVE_H
#define CURVE_H

#include "auxiliary.h"

/* vertex is c[1] for tag=POTRACE_CORNER, and the intersection of
   .c[-1][2]..c[0] and c[1]..c[2] for tag=POTRACE_CURVETO. alpha is only
   defined for tag=POTRACE_CURVETO and is the alpha parameter of the curve:
   .c[-1][2]..c[0] = alpha*(.c[-1][2]..vertex), and
   c[2]..c[1] = alpha*(c[2]..vertex).
   Beta is so that (.beta[i])[.vertex[i],.vertex[i+1]] = .c[i][2].
*/

struct privcurve_s {
  int n;            /* number of segments */
  int *tag;         /* tag[n]: POTRACE_CORNER or POTRACE_CURVETO */
  dpoint_t (*c)[3]; /* c[n][i]: control points. 
		       c[n][0] is unused for tag[n]=POTRACE_CORNER */
  /* the remainder of this structure is special to privcurve, and is
     used in EPS debug output and special EPS "short coding". These
     fields are valid only if "alphacurve" is set. */
  int alphacurve;   /* have the following fields been initialized? */
  dpoint_t *vertex; /* for POTRACE_CORNER, this equals c[1] */
  double *alpha;    /* only for POTRACE_CURVETO */
  double *alpha0;   /* "uncropped" alpha parameter - for debug output only */
  double *beta;
};
typedef struct privcurve_s privcurve_t;

struct sums_s {
  double x;
  double y;
  double x2;
  double xy;
  double y2;
};
typedef struct sums_s sums_t;

/* the path structure is filled in with information about a given path
   as it is accumulated and passed through the different stages of the
   Potrace algorithm. Backends only need to read the fcurve and fm
   fields of this data structure, but debugging backends may read
   other fields. */
struct potrace_privpath_s {
  int len;
  point_t *pt;     /* pt[len]: path as extracted from bitmap */
  int *lon;        /* lon[len]: (i,lon[i]) = longest straight line from i */

  int x0, y0;      /* origin for sums */
  sums_t *sums;    /* sums[len+1]: cache for fast summing */

  int m;           /* length of optimal polygon */
  int *po;         /* po[m]: optimal polygon */

  privcurve_t curve;   /* curve[m]: array of curve elements */
  privcurve_t ocurve;  /* ocurve[om]: array of curve elements */
  privcurve_t *fcurve;  /* final curve: this points to either curve or
		       ocurve. Do not free this separately. */
};
typedef struct potrace_privpath_s potrace_privpath_t;

/* shorter names */
typedef potrace_privpath_t privpath_t;
typedef potrace_path_t path_t;

path_t *path_new(void);
void path_free(path_t *p);
void pathlist_free(path_t *plist);
int privcurve_init(privcurve_t *curve, int n);
void privcurve_to_curve(privcurve_t *pc, potrace_curve_t *c);

#endif /* CURVE_H */



===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/decompose.c =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#ifdef HAVE_INTTYPES_H
#include <inttypes.h>
#endif

#include "potracelib.h"
#include "curve.h"
#include "lists.h"
#include "bitmap.h"
#include "decompose.h"
#include "progress.h"

/* ---------------------------------------------------------------------- */
/* deterministically and efficiently hash (x,y) into a pseudo-random bit */

static inline int detrand(int x, int y) {
  unsigned int z;
  static const unsigned char t[256] = { 
    /* non-linear sequence: constant term of inverse in GF(8), 
       mod x^8+x^4+x^3+x+1 */
    0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 
    0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 
    0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 
    1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 
    0, 0, 1, 1, 1, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 
    0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 
    0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 
    0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 
    1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 
    0, 1, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 
    1, 1, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 
  };

  /* 0x04b3e375 and 0x05a8ef93 are chosen to contain every possible
     5-bit sequence */
  z = ((0x04b3e375 * x) ^ y) * 0x05a8ef93;
  z = t[z & 0xff] ^ t[(z>>8) & 0xff] ^ t[(z>>16) & 0xff] ^ t[(z>>24) & 0xff];
  return z;
}

/* ---------------------------------------------------------------------- */
/* auxiliary bitmap manipulations */

/* set the excess padding to 0 */
static void bm_clearexcess(potrace_bitmap_t *bm) {
  potrace_word mask;
  int y;

  if (bm->w % BM_WORDBITS != 0) {
    mask = BM_ALLBITS << (BM_WORDBITS - (bm->w % BM_WORDBITS));
    for (y=0; y<bm->h; y++) {
      *bm_index(bm, bm->w, y) &= mask;
    }
  }
}

struct bbox_s {
  int x0, x1, y0, y1;    /* bounding box */
};
typedef struct bbox_s bbox_t;

/* clear the bm, assuming the bounding box is set correctly (faster
   than clearing the whole bitmap) */
static void clear_bm_with_bbox(potrace_bitmap_t *bm, bbox_t *bbox) {
  int imin = (bbox->x0 / BM_WORDBITS);
  int imax = ((bbox->x1 + BM_WORDBITS-1) / BM_WORDBITS);
  int i, y;

  for (y=bbox->y0; y<bbox->y1; y++) {
    for (i=imin; i<imax; i++) {
      bm_scanline(bm, y)[i] = 0;
    }
  }
}

/* ---------------------------------------------------------------------- */
/* auxiliary functions */

/* return the "majority" value of bitmap bm at intersection (x,y). We
   assume that the bitmap is balanced at "radius" 1.  */
static int majority(potrace_bitmap_t *bm, int x, int y) {
  int i, a, ct;

  for (i=2; i<5; i++) { /* check at "radius" i */
    ct = 0;
    for (a=-i+1; a<=i-1; a++) {
      ct += BM_GET(bm, x+a, y+i-1) ? 1 : -1;
      ct += BM_GET(bm, x+i-1, y+a-1) ? 1 : -1;
      ct += BM_GET(bm, x+a-1, y-i) ? 1 : -1;
      ct += BM_GET(bm, x-i, y+a) ? 1 : -1;
    }
    if (ct>0) {
      return 1;
    } else if (ct<0) {
      return 0;
    }
  }
  return 0;
}

/* ---------------------------------------------------------------------- */
/* decompose image into paths */

/* efficiently invert bits [x,infty) and [xa,infty) in line y. Here xa
   must be a multiple of BM_WORDBITS. */
static void xor_to_ref(potrace_bitmap_t *bm, int x, int y, int xa) {
  int xhi = x & -BM_WORDBITS;
  int xlo = x & (BM_WORDBITS-1);  /* = x % BM_WORDBITS */
  int i;
  
  if (xhi<xa) {
    for (i = xhi; i < xa; i+=BM_WORDBITS) {
      *bm_index(bm, i, y) ^= BM_ALLBITS;
    }
  } else {
    for (i = xa; i < xhi; i+=BM_WORDBITS) {
      *bm_index(bm, i, y) ^= BM_ALLBITS;
    }
  }
  /* note: the following "if" is needed because x86 treats a<<b as
     a<<(b&31). I spent hours looking for this bug. */
  if (xlo) {
    *bm_index(bm, xhi, y) ^= (BM_ALLBITS << (BM_WORDBITS - xlo));
  }
}

/* a path is represented as an array of points, which are thought to
   lie on the corners of pixels (not on their centers). The path point
   (x,y) is the lower left corner of the pixel (x,y). Paths are
   represented by the len/pt components of a path_t object (which
   also stores other information about the path) */

/* xor the given pixmap with the interior of the given path. Note: the
   path must be within the dimensions of the pixmap. */
static void xor_path(potrace_bitmap_t *bm, path_t *p) {
  int xa, x, y, k, y1;

  if (p->priv->len <= 0) {  /* a path of length 0 is silly, but legal */
    return;
  }

  y1 = p->priv->pt[p->priv->len-1].y;

  xa = p->priv->pt[0].x & -BM_WORDBITS;
  for (k=0; k<p->priv->len; k++) {
    x = p->priv->pt[k].x;
    y = p->priv->pt[k].y;

    if (y != y1) {
      /* efficiently invert the rectangle [x,xa] x [y,y1] */
      xor_to_ref(bm, x, min(y,y1), xa);
      y1 = y;
    }
  }
}

/* Find the bounding box of a given path. Path is assumed to be of
   non-zero length. */
static void setbbox_path(bbox_t *bbox, path_t *p) {
  int x, y;
  int k;

  bbox->y0 = INT_MAX;
  bbox->y1 = 0;
  bbox->x0 = INT_MAX;
  bbox->x1 = 0;

  for (k=0; k<p->priv->len; k++) {
    x = p->priv->pt[k].x;


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/decompose.h =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */


#ifndef DECOMPOSE_H
#define DECOMPOSE_H

#include "potracelib.h"
#include "progress.h"
#include "curve.h"

int bm_to_pathlist(const potrace_bitmap_t *bm, path_t **plistp, const potrace_param_t *param, progress_t *progress);

#endif /* DECOMPOSE_H */



===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/flate.c =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */


/* the PostScript compression module of Potrace. The basic interface
   is through the *_xship function, which processes a byte array and
   outputs it in compressed or verbatim form, depending on whether
   filter is 1 or 0. To flush the output, simply call with the empty
   string and filter=0. filter=2 is used to output encoded text but
   without the PostScript header to turn on the encoding. Each
   function has variants for shipping a single character, a
   null-terminated string, or a byte array. */

/* different compression algorithms are available. There is
   dummy_xship, which is just the identity, and flate_xship, which
   uses zlib compression. Also, lzw_xship provides LZW compression
   from the file lzw.c/h. a85_xship provides a85-encoding without
   compression. Each function returns the actual number of characters
   written. */

/* note: the functions provided here have global state and are not
   reentrant */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>

#ifdef HAVE_ZLIB
#include <zlib.h>
#endif

#include "flate.h"
#include "lzw.h"

#define OUTSIZE 1000

static int a85init(FILE *f);
static int a85finish(FILE *f);
static int a85write(FILE *f, const char *buf, int n);
static int a85out(FILE *f, int n);
static int a85spool(FILE *f, char c);

/* ---------------------------------------------------------------------- */
/* dummy interface: no encoding */

int dummy_xship(FILE *f, int filter, const char *s, int len) {
  fwrite(s, 1, len, f);
  return len;
}

/* ---------------------------------------------------------------------- */
/* flate interface: zlib (=postscript level 3) compression and a85 */

#ifdef HAVE_ZLIB

int pdf_xship(FILE *f, int filter, const char *s, int len) {
	static int fstate = 0;
	static z_stream c_stream;
	char outbuf[OUTSIZE];
	int err;
	int n=0;

  if (filter && !fstate) {
    /* switch on filtering */
    c_stream.zalloc = Z_NULL;
    c_stream.zfree = Z_NULL;
    c_stream.opaque = Z_NULL;
    err = deflateInit(&c_stream, 9);
    if (err != Z_OK) {
      fprintf(stderr, "deflateInit: %s (%d)\n", c_stream.msg, err);
      exit(2);
    }
    c_stream.avail_in = 0;
    fstate = 1;
  } else if (!filter && fstate) {
    /* switch off filtering */
    /* flush stream */
    do {
      c_stream.next_out = (Bytef*)outbuf;
      c_stream.avail_out = OUTSIZE;

      err = deflate(&c_stream, Z_FINISH);
      if (err != Z_OK && err != Z_STREAM_END) {
	fprintf(stderr, "deflate: %s (%d)\n", c_stream.msg, err);
	exit(2);
      }
      n += fwrite(outbuf, 1, OUTSIZE-c_stream.avail_out, f);
    } while (err != Z_STREAM_END);

    fstate = 0;
  }
  if (!fstate) {
    fwrite(s, 1, len, f);
    return n+len;
  }
  
  /* do the actual compression */
  c_stream.next_in = (Bytef*) s;
  c_stream.avail_in = len;

  do {
    c_stream.next_out = (Bytef*) outbuf;
    c_stream.avail_out = OUTSIZE;

    err = deflate(&c_stream, Z_NO_FLUSH);
    if (err != Z_OK) {
      fprintf(stderr, "deflate: %s (%d)\n", c_stream.msg, err);
      exit(2);
    }
    n += fwrite(outbuf, 1, OUTSIZE-c_stream.avail_out, f);
  } while (!c_stream.avail_out);
  
  return n;
}

/* ship len bytes from s using zlib compression. */
int flate_xship(FILE *f, int filter, const char *s, int len) {
  static int fstate = 0;
  static z_stream c_stream;
  char outbuf[OUTSIZE];
  int err;
  int n=0;

  if (filter && !fstate) {
    /* switch on filtering */
    if (filter == 1) {
      n += fprintf(f, "currentfile /ASCII85Decode filter /FlateDecode filter cvx exec\n");
    }
    c_stream.zalloc = Z_NULL;
    c_stream.zfree = Z_NULL;
    c_stream.opaque = Z_NULL;
    err = deflateInit(&c_stream, 9);
    if (err != Z_OK) {
      fprintf(stderr, "deflateInit: %s (%d)\n", c_stream.msg, err);
      exit(2);
    }
    c_stream.avail_in = 0;
    n += a85init(f);
    fstate = 1;
  } else if (!filter && fstate) {
    /* switch off filtering */
    /* flush stream */
    do {
      c_stream.next_out = (Bytef*)outbuf;
      c_stream.avail_out = OUTSIZE;

      err = deflate(&c_stream, Z_FINISH);
      if (err != Z_OK && err != Z_STREAM_END) {
	fprintf(stderr, "deflate: %s (%d)\n", c_stream.msg, err);
	exit(2);
      }
      n += a85write(f, outbuf, OUTSIZE-c_stream.avail_out);
    } while (err != Z_STREAM_END);

    n += a85finish(f);

    fstate = 0;
  }
  if (!fstate) {
    fwrite(s, 1, len, f);
    return n+len;
  }
  
  /* do the actual compression */
  c_stream.next_in = (Bytef*) s;
  c_stream.avail_in = len;

  do {
    c_stream.next_out = (Bytef*) outbuf;
    c_stream.avail_out = OUTSIZE;

    err = deflate(&c_stream, Z_NO_FLUSH);
    if (err != Z_OK) {
      fprintf(stderr, "deflate: %s (%d)\n", c_stream.msg, err);


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/flate.h =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */


#ifndef FLATE_H
#define FLATE_H

int dummy_xship(FILE *f, int filter, const char *s, int len);
int flate_xship(FILE *f, int filter, const char *s, int len);
int pdf_xship(FILE *f, int filter, const char *s, int len);
int lzw_xship(FILE *f, int filter, const char *s, int len);
int a85_xship(FILE *f, int filter, const char *s, int len);

#endif /* FLATE_H */


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/getopt.c =====

/* Getopt for GNU.
   NOTE: getopt is now part of the C library, so if you don't know what
   "Keep this file name-space clean" means, talk to drepper@gnu.org
   before changing it!

   Copyright (C) 1987, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 2000
   	Free Software Foundation, Inc.

   The GNU C Library is free software; you can redistribute it and/or
   modify it under the terms of the GNU Library General Public License as
   published by the Free Software Foundation; either version 2 of the
   License, or (at your option) any later version.

   The GNU C Library is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   Library General Public License for more details.

   You should have received a copy of the GNU Library General Public
   License along with the GNU C Library; see the file COPYING.LIB.  If not,
   write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
   Boston, MA 02110-1301, USA.  */


/* This tells Alpha OSF/1 not to define a getopt prototype in <stdio.h>.
   Ditto for AIX 3.2 and <stdlib.h>.  */
#ifndef _NO_PROTO
# define _NO_PROTO
#endif

#ifdef HAVE_CONFIG_H
# include <config.h>
#endif

#if !defined __STDC__ || !__STDC__
/* This is a separate conditional since some stdc systems
   reject `defined (const)'.  */
# ifndef const
#  define const
# endif
#endif

#include <stdio.h>

/* This needs to come after some library #include
   to get __GNU_LIBRARY__ defined.  */
#ifdef	__GNU_LIBRARY__
/* Don't include stdlib.h for non-GNU C libraries because some of them
   contain conflicting prototypes for getopt.  */
# include <stdlib.h>
# include <unistd.h>
#endif	/* GNU C library.  */

#ifdef VMS
# include <unixlib.h>
# if HAVE_STRING_H - 0
#  include <string.h>
# endif
#endif

#ifndef _
/* This is for other GNU distributions with internationalized messages.  */
# if defined HAVE_LIBINTL_H || defined _LIBC
#  include <libintl.h>
#  ifndef _
#   define _(msgid)	gettext (msgid)
#  endif
# else
#  define _(msgid)	(msgid)
# endif
#endif

/* This version of `getopt' appears to the caller like standard Unix `getopt'
   but it behaves differently for the user, since it allows the user
   to intersperse the options with the other arguments.

   As `getopt' works, it permutes the elements of ARGV so that,
   when it is done, all the options precede everything else.  Thus
   all application programs are extended to handle flexible argument order.

   Setting the environment variable POSIXLY_CORRECT disables permutation.
   Then the behavior is completely standard.

   GNU application programs can use a third alternative mode in which
   they can distinguish the relative order of options and other arguments.  */

#include "getopt.h"

/* For communication from `getopt' to the caller.
   When `getopt' finds an option that takes an argument,
   the argument value is returned here.
   Also, when `ordering' is RETURN_IN_ORDER,
   each non-option ARGV-element is returned here.  */

char *optarg;

/* Index in ARGV of the next element to be scanned.
   This is used for communication to and from the caller
   and for communication between successive calls to `getopt'.

   On entry to `getopt', zero means this is the first call; initialize.

   When `getopt' returns -1, this is the index of the first of the
   non-option elements that the caller should itself scan.

   Otherwise, `optind' communicates from one call to the next
   how much of ARGV has been scanned so far.  */

/* 1003.2 says this must be 1 before any call.  */
int optind = 1;

/* Formerly, initialization of getopt depended on optind==0, which
   causes problems with re-calling getopt as programs generally don't
   know that. */

int __getopt_initialized;

/* The next char to be scanned in the option-element
   in which the last option character we returned was found.
   This allows us to pick up the scan where we left off.

   If this is zero, or a null string, it means resume the scan
   by advancing to the next ARGV-element.  */

static char *nextchar;

/* Callers store zero here to inhibit the error message
   for unrecognized options.  */

int opterr = 1;

/* Set to an option character which was unrecognized.
   This must be initialized on some systems to avoid linking in the
   system's own getopt implementation.  */

int optopt = '?';

/* Describe how to deal with options that follow non-option ARGV-elements.

   If the caller did not specify anything,
   the default is REQUIRE_ORDER if the environment variable
   POSIXLY_CORRECT is defined, PERMUTE otherwise.

   REQUIRE_ORDER means don't recognize them as options;
   stop option processing when the first non-option is seen.
   This is what Unix does.
   This mode of operation is selected by either setting the environment
   variable POSIXLY_CORRECT, or using `+' as the first character
   of the list of option characters.

   PERMUTE is the default.  We permute the contents of ARGV as we scan,
   so that eventually all the non-options are at the end.  This allows options
   to be given in any order, even with programs that were not written to
   expect this.

   RETURN_IN_ORDER is an option available to programs that were written
   to expect options and other ARGV-elements in any order and that care about
   the ordering of the two.  We describe each non-option ARGV-element
   as if it were the argument of an option with character code 1.
   Using `-' as the first character of the list of option characters
   selects this mode of operation.

   The special argument `--' forces an end of option-scanning regardless
   of the value of `ordering'.  In the case of RETURN_IN_ORDER, only
   `--' can cause `getopt' to return -1 with `optind' != ARGC.  */

static enum
{
  REQUIRE_ORDER, PERMUTE, RETURN_IN_ORDER
} ordering;

/* Value of POSIXLY_CORRECT environment variable.  */
static char *posixly_correct;


#ifdef	__GNU_LIBRARY__
/* We want to avoid inclusion of string.h with non-GNU libraries
   because there are many ways it can cause trouble.
   On some systems, it contains special magic macros that don't work
   in GCC.  */


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/getopt.h =====

/* Declarations for getopt.
   Copyright (C) 1989,90,91,92,93,94,96,97,98,99 Free Software Foundation, Inc.
   This file is part of the GNU C Library.

   The GNU C Library is free software; you can redistribute it and/or
   modify it under the terms of the GNU Library General Public License as
   published by the Free Software Foundation; either version 2 of the
   License, or (at your option) any later version.

   The GNU C Library is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   Library General Public License for more details.

   You should have received a copy of the GNU Library General Public
   License along with the GNU C Library; see the file COPYING.LIB.  If not,
   write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
   Boston, MA 02110-1301, USA.  */

#ifndef _GETOPT_H

#ifndef __need_getopt
# define _GETOPT_H 1
#endif

/* If __GNU_LIBRARY__ is not already defined, either we are being used
   standalone, or this is the first header included in the source file.
   If we are being used with glibc, we need to include <features.h>, but
   that does not exist if we are standalone.  So: if __GNU_LIBRARY__ is
   not defined, include <ctype.h>, which will pull in <features.h> for us
   if it's from glibc.  (Why ctype.h?  It's guaranteed to exist and it
   doesn't flood the namespace with stuff the way some other headers do.)  */
#if !defined __GNU_LIBRARY__
# include <ctype.h>
#endif

#ifdef	__cplusplus
extern "C" {
#endif

/* For communication from `getopt' to the caller.
   When `getopt' finds an option that takes an argument,
   the argument value is returned here.
   Also, when `ordering' is RETURN_IN_ORDER,
   each non-option ARGV-element is returned here.  */

extern char *optarg;

/* Index in ARGV of the next element to be scanned.
   This is used for communication to and from the caller
   and for communication between successive calls to `getopt'.

   On entry to `getopt', zero means this is the first call; initialize.

   When `getopt' returns -1, this is the index of the first of the
   non-option elements that the caller should itself scan.

   Otherwise, `optind' communicates from one call to the next
   how much of ARGV has been scanned so far.  */

extern int optind;

/* Callers store zero here to inhibit the error message `getopt' prints
   for unrecognized options.  */

extern int opterr;

/* Set to an option character which was unrecognized.  */

extern int optopt;

#ifndef __need_getopt
/* Describe the long-named options requested by the application.
   The LONG_OPTIONS argument to getopt_long or getopt_long_only is a vector
   of `struct option' terminated by an element containing a name which is
   zero.

   The field `has_arg' is:
   no_argument		(or 0) if the option does not take an argument,
   required_argument	(or 1) if the option requires an argument,
   optional_argument 	(or 2) if the option takes an optional argument.

   If the field `flag' is not NULL, it points to a variable that is set
   to the value given in the field `val' when the option is found, but
   left unchanged if the option is not found.

   To have a long-named option do something other than set an `int' to
   a compiled-in constant, such as set a value from `optarg', set the
   option's `flag' field to zero and its `val' field to a nonzero
   value (the equivalent single-letter option character, if there is
   one).  For long options that have a zero `flag' field, `getopt'
   returns the contents of the `val' field.  */

struct option
{
# if defined __STDC__ && __STDC__
  const char *name;
# else
  char *name;
# endif
  /* has_arg can't be an enum because some compilers complain about
     type mismatches in all the code that assumes it is an int.  */
  int has_arg;
  int *flag;
  int val;
};

/* Names for the values of the `has_arg' field of `struct option'.  */

# define no_argument		0
# define required_argument	1
# define optional_argument	2
#endif	/* need getopt */


/* Get definitions and prototypes for functions to process the
   arguments in ARGV (ARGC of them, minus the program name) for
   options given in OPTS.

   Return the option character from OPTS just read.  Return -1 when
   there are no more options.  For unrecognized options, or options
   missing arguments, `optopt' is set to the option letter, and '?' is
   returned.

   The OPTS string is a list of characters which are recognized option
   letters, optionally followed by colons, specifying that that letter
   takes an argument, to be placed in `optarg'.

   If a letter in OPTS is followed by two colons, its argument is
   optional.  This behavior is specific to the GNU `getopt'.

   The argument `--' causes premature termination of argument
   scanning, explicitly telling `getopt' that there are no more
   options.

   If OPTS begins with `--', then non-option arguments are treated as
   arguments to the option '\0'.  This behavior is specific to the GNU
   `getopt'.  */

#if defined __STDC__ && __STDC__
# ifdef __GNU_LIBRARY__
/* Many other libraries have conflicting prototypes for getopt, with
   differences in the consts, in stdlib.h.  To avoid compilation
   errors, only prototype getopt for the GNU C library.  */
extern int getopt (int argc, char *const *argv, const char *shortopts);
# else /* not __GNU_LIBRARY__ */
extern int getopt ();
# endif /* __GNU_LIBRARY__ */

# ifndef __need_getopt
extern int getopt_long (int argc, char *const *argv, const char *shortopts,
		        const struct option *longopts, int *longind);
extern int getopt_long_only (int argc, char *const *argv,
			     const char *shortopts,
		             const struct option *longopts, int *longind);

/* Internal only.  Users should not call this directly.  */
extern int _getopt_internal (int argc, char *const *argv,
			     const char *shortopts,
		             const struct option *longopts, int *longind,
			     int long_only);
# endif
#else /* not __STDC__ */
extern int getopt ();
# ifndef __need_getopt
extern int getopt_long ();
extern int getopt_long_only ();

extern int _getopt_internal ();
# endif
#endif /* __STDC__ */

#ifdef	__cplusplus
}
#endif

/* Make sure we later can get all the definitions and declarations.  */
#undef __need_getopt

#endif /* getopt.h */


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/getopt1.c =====

/* getopt_long and getopt_long_only entry points for GNU getopt.
   Copyright (C) 1987,88,89,90,91,92,93,94,96,97,98
     Free Software Foundation, Inc.
   This file is part of the GNU C Library.

   The GNU C Library is free software; you can redistribute it and/or
   modify it under the terms of the GNU Library General Public License as
   published by the Free Software Foundation; either version 2 of the
   License, or (at your option) any later version.

   The GNU C Library is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   Library General Public License for more details.

   You should have received a copy of the GNU Library General Public
   License along with the GNU C Library; see the file COPYING.LIB.  If not,
   write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
   Boston, MA 02110-1301, USA.  */


#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "getopt.h"

#if !defined __STDC__ || !__STDC__
/* This is a separate conditional since some stdc systems
   reject `defined (const)'.  */
#ifndef const
#define const
#endif
#endif

#include <stdio.h>

/* This needs to come after some library #include
   to get __GNU_LIBRARY__ defined.  */
#ifdef __GNU_LIBRARY__
#include <stdlib.h>
#endif

#ifndef	NULL
#define NULL 0
#endif

int
getopt_long (argc, argv, options, long_options, opt_index)
     int argc;
     char *const *argv;
     const char *options;
     const struct option *long_options;
     int *opt_index;
{
  return _getopt_internal (argc, argv, options, long_options, opt_index, 0);
}

/* Like getopt_long, but '-' as well as '--' can indicate a long option.
   If an option that starts with '-' (not '--') doesn't match a long option,
   but does match a short option, it is parsed as a short option
   instead.  */

int
getopt_long_only (argc, argv, options, long_options, opt_index)
     int argc;
     char *const *argv;
     const char *options;
     const struct option *long_options;
     int *opt_index;
{
  return _getopt_internal (argc, argv, options, long_options, opt_index, 1);
}




#ifdef TEST

#include <stdio.h>

int
main (argc, argv)
     int argc;
     char **argv;
{
  int c;
  int digit_optind = 0;

  while (1)
    {
      int this_option_optind = optind ? optind : 1;
      int option_index = 0;
      static struct option long_options[] =
      {
	{"add", 1, 0, 0},
	{"append", 0, 0, 0},
	{"delete", 1, 0, 0},
	{"verbose", 0, 0, 0},
	{"create", 0, 0, 0},
	{"file", 1, 0, 0},
	{0, 0, 0, 0}
      };

      c = getopt_long (argc, argv, "abc:d:0123456789",
		       long_options, &option_index);
      if (c == -1)
	break;

      switch (c)
	{
	case 0:
	  printf ("option %s", long_options[option_index].name);
	  if (optarg)
	    printf (" with arg %s", optarg);
	  printf ("\n");
	  break;

	case '0':
	case '1':
	case '2':
	case '3':
	case '4':
	case '5':
	case '6':
	case '7':
	case '8':
	case '9':
	  if (digit_optind != 0 && digit_optind != this_option_optind)
	    printf ("digits occur in two different argv-elements.\n");
	  digit_optind = this_option_optind;
	  printf ("option %c\n", c);
	  break;

	case 'a':
	  printf ("option a\n");
	  break;

	case 'b':
	  printf ("option b\n");
	  break;

	case 'c':
	  printf ("option c with value `%s'\n", optarg);
	  break;

	case 'd':
	  printf ("option d with value `%s'\n", optarg);
	  break;

	case '?':
	  break;

	default:
	  printf ("?? getopt returned character code 0%o ??\n", c);
	}
    }

  if (optind < argc)
    {
      printf ("non-option ARGV-elements: ");
      while (optind < argc)
	printf ("%s ", argv[optind++]);
      printf ("\n");
    }

  exit (0);
}

#endif /* TEST */


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/greymap.c =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */


/* Routines for manipulating greymaps, including reading pgm files. We
   only deal with greymaps of depth 8 bits. */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <errno.h>
#include <stddef.h>
#ifdef HAVE_INTTYPES_H
#include <inttypes.h>
#endif

#include "greymap.h"
#include "bitops.h"

#define INTBITS (8*sizeof(int))

#define mod(a,n) ((a)>=(n) ? (a)%(n) : (a)>=0 ? (a) : (n)-1-(-1-(a))%(n))

static int gm_readbody_pnm(FILE *f, greymap_t **gmp, int magic);
static int gm_readbody_bmp(FILE *f, greymap_t **gmp);

#define TRY(x) if (x) goto try_error
#define TRY_EOF(x) if (x) goto eof
#define TRY_STD(x) if (x) goto std_error

/* ---------------------------------------------------------------------- */
/* basic greymap routines */

/* calculate the size, in bytes, required for the data area of a
   greymap of the given dy and h. Assume h >= 0. Return -1 if the size
   does not fit into the ptrdiff_t type. */
static inline ptrdiff_t getsize(int dy, int h) {
  ptrdiff_t size;

  if (dy < 0) {
    dy = -dy;
  }
  
  size = (ptrdiff_t)dy * (ptrdiff_t)h * (ptrdiff_t)GM_SAMPLESIZE;

  /* check for overflow error */
  if (size < 0 || (h != 0 && dy != 0 && size / h / dy != GM_SAMPLESIZE)) {
    return -1;
  }

  return size;
}

/* return the size, in bytes, of the data area of the greymap. Return
   -1 if the size does not fit into the ptrdiff_t type; however, this
   cannot happen if the bitmap is well-formed, i.e., if created with
   gm_new or gm_dup. */
static inline ptrdiff_t gm_size(const greymap_t *gm) {
  return getsize(gm->dy, gm->h);
}



/* return new greymap initialized to 0. NULL with errno on error.
   Assumes w, h >= 0. */
greymap_t *gm_new(int w, int h) {
  greymap_t *gm;
  int dy = w;
  ptrdiff_t size;

  size = getsize(dy, h);
  if (size < 0) {
    errno = ENOMEM;
    return NULL;
  }
  if (size == 0) {
    size = GM_SAMPLESIZE; /* make sure calloc() doesn't return NULL */
  }
  
  gm = (greymap_t *) malloc(sizeof(greymap_t));
  if (!gm) {
    return NULL;
  }
  gm->w = w;
  gm->h = h;
  gm->dy = dy;
  gm->base = (gm_sample_t *) calloc(1, size);
  if (!gm->base) {
    free(gm);
    return NULL;
  }
  gm->map = gm->base;
  return gm;
}

/* free the given greymap */
void gm_free(greymap_t *gm) {
  if (gm) {
    free(gm->base);
  }
  free(gm);
}

/* duplicate the given greymap. Return NULL on error with errno set. */
greymap_t *gm_dup(greymap_t *gm) {
  greymap_t *gm1 = gm_new(gm->w, gm->h);
  int y;
  
  if (!gm1) {
    return NULL;
  }
  for (y=0; y<gm->h; y++) {
    memcpy(gm_scanline(gm1, y), gm_scanline(gm, y), (size_t)gm1->dy * GM_SAMPLESIZE);
  }
  return gm1;
}

/* clear the given greymap to color b. */
void gm_clear(greymap_t *gm, int b) {
  ptrdiff_t size = gm_size(gm);
  int x, y;
  
  if (b==0) {
    memset(gm->base, 0, size);
  } else {
    for (y=0; y<gm->h; y++) {
      for (x=0; x<gm->w; x++) {
        GM_UPUT(gm, x, y, b);
      }
    }
  }
}

/* turn the given greymap upside down. This does not move the pixel
   data or change the base address. */
static inline void gm_flip(greymap_t *gm) {
  int dy = gm->dy;

  if (gm->h == 0 || gm->h == 1) {
    return;
  }
  
  gm->map = gm_scanline(gm, gm->h - 1);
  gm->dy = -dy;
}

/* resize the greymap to the given new height. The pixel data remains
   bottom-aligned (truncated at the top) when dy >= 0 and top-aligned
   (truncated at the bottom) when dy < 0. Return 0 on success, or 1 on
   error with errno set. If the new height is <= the old one, no error
   should occur. If the new height is larger, the additional pixel
   data is *not* initialized. */
static inline int gm_resize(greymap_t *gm, int h) {
  int dy = gm->dy;
  ptrdiff_t newsize;
  gm_sample_t *newbase;

  if (dy < 0) {
    gm_flip(gm);
  }
  
  newsize = getsize(dy, h);
  if (newsize < 0) {
    errno = ENOMEM;
    goto error;
  }
  if (newsize == 0) {
    newsize = GM_SAMPLESIZE; /* make sure realloc() doesn't return NULL */
  }
  
  newbase = (gm_sample_t *)realloc(gm->base, newsize);
  if (newbase == NULL) {
    goto error;
  }
  gm->base = newbase;


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/greymap.h =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */


#ifndef GREYMAP_H
#define GREYMAP_H

#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>

/* type for greymap samples */
typedef signed short int gm_sample_t;

#define GM_SAMPLESIZE (sizeof(gm_sample_t))

/* internal format for greymaps. Note: in this format, rows are
   ordered from bottom to top. The pixels in each row are given from
   left to right. */
struct greymap_s {
  int w;              /* width, in pixels */
  int h;              /* height, in pixels */
  int dy;             /* offset between scanlines (in samples); 
                         can be negative */
  gm_sample_t *base;  /* root of allocated data */
  gm_sample_t *map;   /* points to the lower left pixel */
};
typedef struct greymap_s greymap_t;

/* macros for accessing pixel at index (x,y). Note that the origin is
   in the *lower* left corner. U* macros omit the bounds check. */

#define gm_scanline(gm, y) ((gm)->map + (ptrdiff_t)(y)*(ptrdiff_t)(gm)->dy)
#define gm_index(gm, x, y) (gm_scanline(gm, y) + (x))
#define gm_safe(gm, x, y) ((int)(x)>=0 && (int)(x)<(gm)->w && (int)(y)>=0 && (int)(y)<(gm)->h)
#define gm_bound(x, m) ((x)<0 ? 0 : (x)>=(m) ? (m)-1 : (x))
#define GM_UGET(gm, x, y) (*gm_index(gm, x, y))
#define GM_UINC(gm, x, y, b) (*gm_index(gm, x, y) += (gm_sample_t)(b))
#define GM_UINV(gm, x, y) (*gm_index(gm, x, y) = 255 - *gm_index(gm, x, y))
#define GM_UPUT(gm, x, y, b) (*gm_index(gm, x, y) = (gm_sample_t)(b))
#define GM_GET(gm, x, y) (gm_safe(gm, x, y) ? GM_UGET(gm, x, y) : 0)
#define GM_INC(gm, x, y, b) (gm_safe(gm, x, y) ? GM_UINC(gm, x, y, b) : 0)
#define GM_INV(gm, x, y) (gm_safe(gm, x, y) ? GM_UINV(gm, x, y) : 0)
#define GM_PUT(gm, x, y, b) (gm_safe(gm, x, y) ? GM_UPUT(gm, x, y, b) : 0)
#define GM_BGET(gm, x, y) ((gm)->w == 0 || (gm)->h == 0 ? 0 : GM_UGET(gm, gm_bound(x, (gm)->w), gm_bound(y, (gm)->h)))

/* modes for cutting off out-of-range values. The following names
   refer to winding numbers. I.e., make a pixel black if winding
   number is nonzero, odd, or positive, respectively. We assume that 0
   winding number corresponds to white (255). */
#define GM_MODE_NONZERO 1
#define GM_MODE_ODD 2
#define GM_MODE_POSITIVE 3
#define GM_MODE_NEGATIVE 4

extern const char *gm_read_error;

greymap_t *gm_new(int w, int h);
greymap_t *gm_dup(greymap_t *gm);
void gm_free(greymap_t *gm);
void gm_clear(greymap_t *gm, int b);
int gm_read(FILE *f, greymap_t **gmp);
int gm_writepgm(FILE *f, greymap_t *gm, const char *comment, int raw, int mode, double gamma);
int gm_print(FILE *f, greymap_t *gm);

#endif /* GREYMAP_H */


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/include/getopt/getopt.h =====

/* Declarations for getopt.
   Copyright (C) 1989,90,91,92,93,94,96,97,98,99 Free Software Foundation, Inc.
   This file is part of the GNU C Library.

   The GNU C Library is free software; you can redistribute it and/or
   modify it under the terms of the GNU Library General Public License as
   published by the Free Software Foundation; either version 2 of the
   License, or (at your option) any later version.

   The GNU C Library is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   Library General Public License for more details.

   You should have received a copy of the GNU Library General Public
   License along with the GNU C Library; see the file COPYING.LIB.  If not,
   write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
   Boston, MA 02110-1301, USA.  */

#ifndef _GETOPT_H

#ifndef __need_getopt
# define _GETOPT_H 1
#endif

/* If __GNU_LIBRARY__ is not already defined, either we are being used
   standalone, or this is the first header included in the source file.
   If we are being used with glibc, we need to include <features.h>, but
   that does not exist if we are standalone.  So: if __GNU_LIBRARY__ is
   not defined, include <ctype.h>, which will pull in <features.h> for us
   if it's from glibc.  (Why ctype.h?  It's guaranteed to exist and it
   doesn't flood the namespace with stuff the way some other headers do.)  */
#if !defined __GNU_LIBRARY__
# include <ctype.h>
#endif

#ifdef	__cplusplus
extern "C" {
#endif

/* For communication from `getopt' to the caller.
   When `getopt' finds an option that takes an argument,
   the argument value is returned here.
   Also, when `ordering' is RETURN_IN_ORDER,
   each non-option ARGV-element is returned here.  */

extern char *optarg;

/* Index in ARGV of the next element to be scanned.
   This is used for communication to and from the caller
   and for communication between successive calls to `getopt'.

   On entry to `getopt', zero means this is the first call; initialize.

   When `getopt' returns -1, this is the index of the first of the
   non-option elements that the caller should itself scan.

   Otherwise, `optind' communicates from one call to the next
   how much of ARGV has been scanned so far.  */

extern int optind;

/* Callers store zero here to inhibit the error message `getopt' prints
   for unrecognized options.  */

extern int opterr;

/* Set to an option character which was unrecognized.  */

extern int optopt;

#ifndef __need_getopt
/* Describe the long-named options requested by the application.
   The LONG_OPTIONS argument to getopt_long or getopt_long_only is a vector
   of `struct option' terminated by an element containing a name which is
   zero.

   The field `has_arg' is:
   no_argument		(or 0) if the option does not take an argument,
   required_argument	(or 1) if the option requires an argument,
   optional_argument 	(or 2) if the option takes an optional argument.

   If the field `flag' is not NULL, it points to a variable that is set
   to the value given in the field `val' when the option is found, but
   left unchanged if the option is not found.

   To have a long-named option do something other than set an `int' to
   a compiled-in constant, such as set a value from `optarg', set the
   option's `flag' field to zero and its `val' field to a nonzero
   value (the equivalent single-letter option character, if there is
   one).  For long options that have a zero `flag' field, `getopt'
   returns the contents of the `val' field.  */

struct option
{
# if defined __STDC__ && __STDC__
  const char *name;
# else
  char *name;
# endif
  /* has_arg can't be an enum because some compilers complain about
     type mismatches in all the code that assumes it is an int.  */
  int has_arg;
  int *flag;
  int val;
};

/* Names for the values of the `has_arg' field of `struct option'.  */

# define no_argument		0
# define required_argument	1
# define optional_argument	2
#endif	/* need getopt */


/* Get definitions and prototypes for functions to process the
   arguments in ARGV (ARGC of them, minus the program name) for
   options given in OPTS.

   Return the option character from OPTS just read.  Return -1 when
   there are no more options.  For unrecognized options, or options
   missing arguments, `optopt' is set to the option letter, and '?' is
   returned.

   The OPTS string is a list of characters which are recognized option
   letters, optionally followed by colons, specifying that that letter
   takes an argument, to be placed in `optarg'.

   If a letter in OPTS is followed by two colons, its argument is
   optional.  This behavior is specific to the GNU `getopt'.

   The argument `--' causes premature termination of argument
   scanning, explicitly telling `getopt' that there are no more
   options.

   If OPTS begins with `--', then non-option arguments are treated as
   arguments to the option '\0'.  This behavior is specific to the GNU
   `getopt'.  */

#if defined __STDC__ && __STDC__
# ifdef __GNU_LIBRARY__
/* Many other libraries have conflicting prototypes for getopt, with
   differences in the consts, in stdlib.h.  To avoid compilation
   errors, only prototype getopt for the GNU C library.  */
extern int getopt (int argc, char *const *argv, const char *shortopts);
# else /* not __GNU_LIBRARY__ */
extern int getopt ();
# endif /* __GNU_LIBRARY__ */

# ifndef __need_getopt
extern int getopt_long (int argc, char *const *argv, const char *shortopts,
		        const struct option *longopts, int *longind);
extern int getopt_long_only (int argc, char *const *argv,
			     const char *shortopts,
		             const struct option *longopts, int *longind);

/* Internal only.  Users should not call this directly.  */
extern int _getopt_internal (int argc, char *const *argv,
			     const char *shortopts,
		             const struct option *longopts, int *longind,
			     int long_only);
# endif
#else /* not __STDC__ */
extern int getopt ();
# ifndef __need_getopt
extern int getopt_long ();
extern int getopt_long_only ();

extern int _getopt_internal ();
# endif
#endif /* __STDC__ */

#ifdef	__cplusplus
}
#endif

/* Make sure we later can get all the definitions and declarations.  */
#undef __need_getopt

#endif /* getopt.h */


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/lists.h =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */


#ifndef _PS_LISTS_H
#define _PS_LISTS_H

/* here we define some general list macros. Because they are macros,
   they should work on any datatype with a "->next" component. Some of
   them use a "hook". If elt and list are of type t* then hook is of
   type t**. A hook stands for an insertion point in the list, i.e.,
   either before the first element, or between two elements, or after
   the last element. If an operation "sets the hook" for an element,
   then the hook is set to just before the element. One can insert
   something at a hook. One can also unlink at a hook: this means,
   unlink the element just after the hook. By "to unlink", we mean the
   element is removed from the list, but not deleted. Thus, it and its
   components still need to be freed. */

/* Note: these macros are somewhat experimental. Only the ones that
   are actually *used* have been tested. So be careful to test any
   that you use. Looking at the output of the preprocessor, "gcc -E"
   (possibly piped though "indent"), might help too. Also: these
   macros define some internal (local) variables that start with
   "_". */

/* we enclose macro definitions whose body consists of more than one
   statement in MACRO_BEGIN and MACRO_END, rather than '{' and '}'.  The
   reason is that we want to be able to use the macro in a context
   such as "if (...) macro(...); else ...". If we didn't use this obscure
   trick, we'd have to omit the ";" in such cases. */

#define MACRO_BEGIN do {
#define MACRO_END   } while (0)

/* ---------------------------------------------------------------------- */
/* macros for singly-linked lists */

/* traverse list. At the end, elt is set to NULL. */
#define list_forall(elt, list)   for (elt=list; elt!=NULL; elt=elt->next)

/* set elt to the first element of list satisfying boolean condition
   c, or NULL if not found */
#define list_find(elt, list, c) \
  MACRO_BEGIN list_forall(elt, list) if (c) break; MACRO_END

/* like forall, except also set hook for elt. */
#define list_forall2(elt, list, hook) \
  for (elt=list, hook=&list; elt!=NULL; hook=&elt->next, elt=elt->next)

/* same as list_find, except also set hook for elt. */
#define list_find2(elt, list, c, hook) \
  MACRO_BEGIN list_forall2(elt, list, hook) if (c) break; MACRO_END

/* same, except only use hook. */
#define _list_forall_hook(list, hook) \
  for (hook=&list; *hook!=NULL; hook=&(*hook)->next)

/* same, except only use hook. Note: c may only refer to *hook, not elt. */
#define _list_find_hook(list, c, hook) \
  MACRO_BEGIN _list_forall_hook(list, hook) if (c) break; MACRO_END

/* insert element after hook */
#define list_insert_athook(elt, hook) \
  MACRO_BEGIN elt->next = *hook; *hook = elt; MACRO_END

/* insert element before hook */
#define list_insert_beforehook(elt, hook) \
  MACRO_BEGIN elt->next = *hook; *hook = elt; hook=&elt->next; MACRO_END

/* unlink element after hook, let elt be unlinked element, or NULL.
   hook remains. */
#define list_unlink_athook(list, elt, hook) \
  MACRO_BEGIN \
  elt = hook ? *hook : NULL; if (elt) { *hook = elt->next; elt->next = NULL; }\
  MACRO_END

/* unlink the specific element, if it is in the list. Otherwise, set
   elt to NULL */
#define list_unlink(listtype, list, elt)      \
  MACRO_BEGIN  	       	       	       	      \
  listtype **_hook;			      \
  _list_find_hook(list, *_hook==elt, _hook);  \
  list_unlink_athook(list, elt, _hook);	      \
  MACRO_END

/* prepend elt to list */
#define list_prepend(list, elt) \
  MACRO_BEGIN elt->next = list; list = elt; MACRO_END

/* append elt to list. */
#define list_append(listtype, list, elt)     \
  MACRO_BEGIN                                \
  listtype **_hook;                          \
  _list_forall_hook(list, _hook) {}          \
  list_insert_athook(elt, _hook);            \
  MACRO_END

/* unlink the first element that satisfies the condition. */
#define list_unlink_cond(listtype, list, elt, c)     \
  MACRO_BEGIN                                        \
  listtype **_hook;			  	     \
  list_find2(elt, list, c, _hook);                   \
  list_unlink_athook(list, elt, _hook);              \
  MACRO_END

/* let elt be the nth element of the list, starting to count from 0.
   Return NULL if out of bounds.   */
#define list_nth(elt, list, n)                                \
  MACRO_BEGIN                                                 \
  int _x;  /* only evaluate n once */                         \
  for (_x=(n), elt=list; _x && elt; _x--, elt=elt->next) {}   \
  MACRO_END

/* let elt be the nth element of the list, starting to count from 0.
   Return NULL if out of bounds.   */
#define list_nth_hook(elt, list, n, hook)                     \
  MACRO_BEGIN                                                 \
  int _x;  /* only evaluate n once */                         \
  for (_x=(n), elt=list, hook=&list; _x && elt; _x--, hook=&elt->next, elt=elt->next) {}   \
  MACRO_END

/* set n to the length of the list */
#define list_length(listtype, list, n)                   \
  MACRO_BEGIN          	       	       	       	       	 \
  listtype *_elt;   			 		 \
  n=0;					 		 \
  list_forall(_elt, list) 		 		 \
    n++;				 		 \
  MACRO_END

/* set n to the index of the first element satisfying cond, or -1 if
   none found. Also set elt to the element, or NULL if none found. */
#define list_index(list, n, elt, c)                      \
  MACRO_BEGIN				 		 \
  n=0;					 		 \
  list_forall(elt, list) {		 		 \
    if (c) break;			 		 \
    n++;				 		 \
  }					 		 \
  if (!elt)				 		 \
    n=-1;				 		 \
  MACRO_END

/* set n to the number of elements in the list that satisfy condition c */
#define list_count(list, n, elt, c)                      \
  MACRO_BEGIN				 		 \
  n=0;					 		 \
  list_forall(elt, list) {		 		 \
    if (c) n++;				 		 \
  }                                                      \
  MACRO_END

/* let elt be each element of the list, unlinked. At the end, set list=NULL. */
#define list_forall_unlink(elt, list) \
  for (elt=list; elt ? (list=elt->next, elt->next=NULL), 1 : 0; elt=list)

/* reverse a list (efficient) */
#define list_reverse(listtype, list)            \
  MACRO_BEGIN				 	\
  listtype *_list1=NULL, *elt;			\
  list_forall_unlink(elt, list) 		\
    list_prepend(_list1, elt);			\
  list = _list1;				\
  MACRO_END

/* insert the element ELT just before the first element TMP of the
   list for which COND holds. Here COND must be a condition of ELT and
   TMP.  Typical usage is to insert an element into an ordered list:
   for instance, list_insert_ordered(listtype, list, elt, tmp,
   elt->size <= tmp->size).  Note: if we give a "less than or equal"
   condition, the new element will be inserted just before a sequence
   of equal elements. If we give a "less than" condition, the new
   element will be inserted just after a list of equal elements.
   Note: it is much more efficient to construct a list with
   list_prepend and then order it with list_merge_sort, than to
   construct it with list_insert_ordered. */
#define list_insert_ordered(listtype, list, elt, tmp, cond) \
  MACRO_BEGIN                                               \


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/lzw.c =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */


/* code for adaptive LZW compression, as used in PostScript. */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>

#include "lists.h"
#include "bitops.h"
#include "lzw.h"

/* ---------------------------------------------------------------------- */
/* compression state specification */

/* The compression algorithm follows the following specification,
   expressed as a state machine. A state is a triple {s,d,n}, where s
   is a string of input symbols, d is a dictionary, which is a
   function from strings to output symbols, and n is the dictionary
   size, or equivalently, the next unused output symbol. There are
   also special states init and stop. emit[b, code] is a function
   which emits the code 'code' as a b-bit value into the output
   bitstream. hibit(n) returns the least number of binary digits
   required to represent n.

   init ---> {[], newdict, 258}

     where [] is the empty string, and newdict maps each of the 256
     singleton strings to itself. (Note that there are two special
     output symbols 256 and 257, so that the next available one is
     258). Note: hibit(258)=9.

   {[], d, n} (input c) ---> (emit[hibit(n), 256]) {c, d, n}

   {s,d,n} (input c) ---> {s*c,d,n}

     if s!=[], s*c is in the domain of d. Here s*c is the strings s
     extended by the character c.

   {s,d,n} (input c) ---> (emit[hibit(n), d(s)]) {c,d',n+1}

     if s!=[], s*c is not in the domain of d, and hibit(n+2) <= 12.
     Here d'=d+{s*c->n}.

   {s,d,n} (input c) ---> 
           (emit[hibit(n), d(s)]) (emit[hibit(n+1), 256]) {c, newdict, 258}

     if s!=[], s*c is not in the domain of d, and hibit(n+2) > 12.

   {s,d,n} (input EOD) ---> (emit[hibit(n), d(s)]) (emit[hibit(n+1), 257]) stop

     where s != []. Here, EOD stands for end-of-data.

   {[],d,n} (input EOD) ---> (emit[hibit(n), 256]) (emit[hibit(n), 257]) stop

   Notes: 

   * Each reachable state {s,d,n} satisfies hibit(n+1) <= 12.
   * Only codes of 12 or fewer bits are emitted.
   * Each reachable state {s,d,n} satisfies s=[] or s is in the domain of d.
   * The domain of d is always prefix closed (except for the empty prefix)
   * The state machine is deterministic and non-blocking.

*/
   

/* ---------------------------------------------------------------------- */
/* private state */

#define BITBUF_TYPE unsigned int

/* the dictionary is implemented as a tree of strings under the prefix
   order. The tree is in turns represented as a linked list of
   lzw_dict_t structures, with "children" pointing to a node's first
   child, and "next" pointing to a node's next sibling. As an
   optimization, the top-level nodes (singleton strings) are
   implemented lazily, i.e., the corresponding entry is not actually
   created until it is accessed. */

struct lzw_dict_s {
  char c;            /* last character of string represented by this entry */
  unsigned int code; /* code for the string represented by this entry */
  int freq;          /* how often searched? For optimization only */
  struct lzw_dict_s *children;  /* list of sub-entries */
  struct lzw_dict_s *next;      /* for making a linked list */
};
typedef struct lzw_dict_s lzw_dict_t;

/* A state {s,d,n} is represented by the "dictionary state" part of
   the lzw_state_t structure. Here, s is a pointer directly to the node
   of the dictionary structure corresponding to the string s, or NULL
   if s=[]. Further, the lzw_state_t structure contains a buffer of
   pending output bits, and a flag indicating whether the EOD (end of
   data) has been reached in the input. */

struct lzw_state_s {
  /* dictionary state */
  int n;           /* current size of the dictionary */
  lzw_dict_t *d;   /* pointer to dictionary */
  lzw_dict_t *s;   /* pointer to current string, or NULL at beginning */

  /* buffers for pending output */
  BITBUF_TYPE buf; /* bits scheduled for output - left aligned, 0 padded */
  int bufsize;     /* number of bits scheduled for output. */
  int eod;         /* flush buffer? */
};
typedef struct lzw_state_s lzw_state_t;

/* ---------------------------------------------------------------------- */
/* auxiliary functions which operate on dictionary states */

/* recursively free an lzw_dict_t object */
static void lzw_free_dict(lzw_dict_t *s) {
  lzw_dict_t *e;

  list_forall_unlink(e, s) {
    lzw_free_dict(e->children);
    free(e);
  }
}

/* re-initialize the lzw state's dictionary state to "newdict",
   freeing any old dictionary. */
static void lzw_clear_table(lzw_state_t *st) {

  lzw_free_dict(st->d);
  st->d = NULL;
  st->n = 258;
  st->s = NULL;
}

/* ---------------------------------------------------------------------- */
/* auxiliary functions for reading/writing the bit buffer */

/* write the code to the bit buffer. Precondition st->bufsize <= 7.
   Note: this does not change the dictionary state; in particular,
   n must be updated between consecutive calls. */
static inline void lzw_emit(unsigned int code, lzw_state_t *st) {
  BITBUF_TYPE mask;
  int bits = hibit(st->n);

  /* fill bit buffer */
  mask = (1 << bits) - 1;
  code &= mask;

  st->buf |= code << (8*sizeof(BITBUF_TYPE) - st->bufsize - bits);
  st->bufsize += bits;
}

/* transfer one byte from bit buffer to output. Precondition:
   s->avail_out > 0. */
static inline void lzw_read_bitbuf(lzw_stream_t *s) {
  int ch;
  lzw_state_t *st = (lzw_state_t *)s->internal;

  ch = st->buf >> (8*sizeof(BITBUF_TYPE)-8);
  st->buf <<= 8;
  st->bufsize -= 8;

  s->next_out[0] = ch;
  s->next_out++;
  s->avail_out--;
}

/* ---------------------------------------------------------------------- */
/* The following functions implement the state machine. */

/* perform state transition of the state st on input character
   ch. This updates the dictionary state and/or writes to the bit
   buffer. Precondition: st->bufsize <= 7. Return 0 on success, or 1
   on error with errno set. */
static int lzw_encode_char(lzw_state_t *st, char c) {


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/src/lzw.h =====

/* Copyright (C) 2001-2019 Peter Selinger.
   This file is part of Potrace. It is free software and it is covered
   by the GNU General Public License. See the file COPYING for details. */


#define LZW_NORMAL 0
#define LZW_EOD 1

/* user visible state */

struct lzw_stream_s {
  const char *next_in; /* pointer to next input character */
  int avail_in;        /* number of input chars available */
  char *next_out;      /* pointer to next free byte in output buffer */
  int avail_out;  
