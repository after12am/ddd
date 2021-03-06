<!DOCTYPE html>
<!--[if IE 8]><html class="no-js lt-ie9" lang="en" > <![endif]-->
<!--[if gt IE 8]><!--> <html class="no-js" lang="en" > <!--<![endif]-->
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Welcome to {{database.name}} - {{database.name}} {{version}} database design documentation</title>
<link href='https://fonts.googleapis.com/css?family=Lato:400,700,400italic,700italic|Roboto+Slab:400,700|Inconsolata:400,700' rel='stylesheet' type='text/css'>
<link rel="stylesheet" href="static/css/theme.css" type="text/css" />
<link rel="stylesheet" href="static/css/custom.css" type="text/css" />
<link rel="top" title="{{database.name}} {{version}} database documentation" href="#"/>
<script src="https://cdnjs.cloudflare.com/ajax/libs/modernizr/2.6.2/modernizr.min.js"></script>
</head>
<body class="wy-body-for-nav" role="document">
    <div class="wy-grid-for-nav">
        <nav data-toggle="wy-nav-shift" class="wy-nav-side">
            <div class="wy-side-nav-search">
                <a href="/" class="fa fa-home"> {{database.name}}</a>
                <div role="search">
                    <input class="search" type="text" name="q" placeholder="Search word" />
                </div>
            </div>
            <div class="wy-menu wy-menu-vertical" data-spy="affix" role="navigation" aria-label="main navigation">
                <ul class="simple">
                    {% for table in database.tables %}
                        <li class="toctree-l1" data-hash="{{table}}"><a class="{{table}}" href="#{{table}}">{{table}}</a></li>
                    {% endfor %}
                </ul>
            </div>
            &nbsp;
        </nav>
        <section data-toggle="wy-nav-shift" class="wy-nav-content-wrap">
            <nav class="wy-nav-top" role="navigation" aria-label="top navigation">
                <i data-toggle="wy-nav-top" class="fa fa-bars"></i>
                <a href="#">{{database.name}}</a>
            </nav>
            <div class="wy-nav-content">
                <div class="rst-content">
                    <div class="navigation" role="navigation" aria-label="breadcrumbs navigation">
                        <ul class="wy-breadcrumbs">
                            <li>Welcome to {{database.name}}</li>
                            <li class="wy-breadcrumbs-aside">
                                <a href="sql.txt"> View SQL</a>
                            </li>
                          </ul>
                        <hr/>
                    </div>
                    <div role="main" class="document">
                        <div class="error" style="display: none">
                            <h2>Oops! Sorry,</h2>
                            <p>Your search did not match any documents. Please make sure that all words are spelled correctly.</p>
                        </div>
                        {% for table, item in database.tables.iteritems() %}
                            <div id="{{table}}" class="section">
                                <div class="header">
                                    <h2 id="{{table}}">{{table}}<a class="headerlink" href="#{{table}}" title="Permalink to this headline">¶</a></h2>
                                    <p>{{item.comment}}</p>
                                </div>
                                <div>
                                    {% include "elements/table_status.ctp" %}
                                </div>
                                <hr/>
                            </div>
                        {% endfor %}
                    </div>
                    <footer>
                        <div role="contentinfo">
                            <p>&copy; Copyright {{today.year}}, {{author}}.</p>
                        </div>
                        <a href="https://github.com/snide/sphinx_rtd_theme">Sphinx theme</a> provided by <a href="https://readthedocs.org">Read the Docs</a>
                    </footer>
                </div>
            </div>
        </section>
    </div>
<script type="text/javascript" src="static/js/jquery.js"></script>
<script type="text/javascript" src="static/js/underscore.js"></script>
<script type="text/javascript" src="static/js/jquery.highlight-4.closure.js"></script>
<script type="text/javascript" src="static/js/theme.js"></script>
</body>
</html>