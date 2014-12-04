/*
 * Project: Farnsworth
 * Authors: Karandeep Singh Nagra and Nader Morshed
 */

CKEDITOR.editorConfig = function( config ) {
    /* Define extra plugins to load */
    config.extraPlugins = 'widget,lineutils,pbckcode,mathjax,leaflet,autolink,codemirror,footnotes,oembed,imagebrowser,symbol,dialog,slideshow';

    /* Define the toolbar, item by item */
    config.toolbar = [
        { name: 'editing', items: ['Bold', 'Italic', 'Underline','Strike', 'Subscript', 'Superscript', '-', 'Link', 'Unlink', 'Anchor'] },
        { name: 'document', items: ['Cut', 'Copy', 'Paste', '-', 'Find', 'Replace', 'Scayt', '-', 'Undo', 'Redo'] },
        '/',
        { name: 'paragraph', items: ['NumberedList', 'BulletedList', 'JustifyLeft', 'JustifyCenter', 'JustifyBlock', 'JustifyRight', '-', 'Outdent', 'Indent', '-', 'Blockquote', 'CreateDiv'] },
        { name: 'others', items: ['Image', 'Slideshow', 'HorizontalRule', 'Smiley', 'oembed', 'Symbol', '-', 'pbckcode', 'Mathjax', 'leaflet', 'Footnotes'] },
        '/',
        { name: 'styles', items: ['Styles', 'Format', 'Font', 'FontSize'] },
        { name: 'colors', items: ['TextColor', 'BGColor' ] },
        ];

    /* configure pbckcode */
    config.pbckcode = {
        modes: [
            ['C/C++'        , 'c_pp'],
            ['C9Search'     , 'c9search'],
            ['Clojure'      , 'clojure'],
            ['CoffeeScript' , 'coffee'],
            ['ColdFusion'   , 'coldfusion'],
            ['C#'           , 'csharp'],
            ['CSS'          , 'css'],
            ['Diff'         , 'diff'],
            ['Glsl'         , 'glsl'],
            ['Go'           , 'golang'],
            ['Groovy'       , 'groovy'],
            ['haXe'         , 'haxe'],
            ['HTML'         , 'html'],
            ['Jade'         , 'jade'],
            ['Java'         , 'java'],
            ['JavaScript'   , 'javascript'],
            ['JSON'         , 'json'],
            ['JSP'          , 'jsp'],
            ['JSX'          , 'jsx'],
            ['LaTeX'        , 'latex'],
            ['LESS'         , 'less'],
            ['Liquid'       , 'liquid'],
            ['Lua'          , 'lua'],
            ['LuaPage'      , 'luapage'],
            ['Markdown'     , 'markdown'],
            ['OCaml'        , 'ocaml'],
            ['Perl'         , 'perl'],
            ['pgSQL'        , 'pgsql'],
            ['PHP'          , 'php'],
            ['Powershell'   , 'powershel1'],
            ['Python'       , 'python'],
            ['Ruby'         , 'ruby'],
            ['OpenSCAD'     , 'scad'],
            ['Scala'        , 'scala'],
            ['SCSS/Sass'    , 'scss'],
            ['SH'           , 'sh'],
            ['SQL'          , 'sql'],
            ['SVG'          , 'svg'],
            ['Tcl'          , 'tcl'],
            ['Text'         , 'text'],
            ['Textile'      , 'textile'],
            ['XML'          , 'xml'],
            ['XQuery'       , 'xq'],
            ['YAML'         , 'yaml']
        ],
        tab_size: '4'
    };
};
