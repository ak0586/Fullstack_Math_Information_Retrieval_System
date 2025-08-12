// web_html_viewer.dart
// Web-specific HTML viewer with proper MathML and HTML rendering
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:html' as html;
import 'dart:ui_web' as ui_web;

class WebFileViewerPage extends StatefulWidget {
  final String fileId;
  final String filename;
  final String baseUrl;

  const WebFileViewerPage({
    required this.fileId,
    required this.filename,
    required this.baseUrl,
    Key? key,
  }) : super(key: key);

  @override
  _WebFileViewerPageState createState() => _WebFileViewerPageState();
}

class _WebFileViewerPageState extends State<WebFileViewerPage> {
  bool isLoading = true;
  bool hasError = false;
  late String viewId;

  @override
  void initState() {
    super.initState();
    viewId =
        'html-viewer-${widget.fileId}-${DateTime.now().millisecondsSinceEpoch}';
    loadFile();
  }

  Future<void> loadFile() async {
    setState(() {
      isLoading = true;
      hasError = false;
    });

    try {
      final response = await http.get(
        Uri.parse('${widget.baseUrl}/view/${widget.fileId}'),
      );

      if (response.statusCode == 200) {
        // Create enhanced HTML with better MathML support for web
        final enhancedHtml = _createEnhancedHtml(response.body);

        // Create iframe element
        final iframeElement = html.IFrameElement()
          ..style.width = '100%'
          ..style.height = '100%'
          ..style.border = 'none'
          ..srcdoc = enhancedHtml;

        // Register the iframe element
        ui_web.platformViewRegistry.registerViewFactory(
          viewId,
          (int viewId) => iframeElement,
        );

        setState(() {
          isLoading = false;
          hasError = false;
        });
      } else {
        setState(() {
          isLoading = false;
          hasError = true;
        });
      }
    } catch (e) {
      print('Error loading file: $e');
      setState(() {
        isLoading = false;
        hasError = true;
      });
    }
  }

  String _createEnhancedHtml(String htmlContent) {
    return '''
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <script type="text/javascript" id="MathJax-script" async
      src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/mml-chtml.js">
    </script>
    <style>
      body {
        margin: 10px;
        padding: 5px;
        font-family: sans-serif;
      }
      mjx-container {
        all: unset;
        display: inline;
      }
      mjx-container[display="block"] {
        display: block;
        text-align: left;
      }
    </style>
  </head>
  <body>
    $htmlContent
  </body>
</html>
''';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: Text(
          widget.filename,
          style: const TextStyle(
            fontWeight: FontWeight.w500,
            color: Colors.white,
            fontSize: 16,
          ),
        ),
        backgroundColor: Colors.deepPurple,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.white),
            onPressed: () {
              loadFile();
            },
          ),
        ],
      ),
      body: isLoading
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(
                    valueColor: AlwaysStoppedAnimation<Color>(
                      Colors.deepPurple,
                    ),
                  ),
                  SizedBox(height: 16),
                  Text(
                    'Loading file...',
                    style: TextStyle(color: Colors.grey, fontSize: 16),
                  ),
                ],
              ),
            )
          : hasError
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.error_outline, size: 60, color: Colors.red[400]),
                  const SizedBox(height: 16),
                  const Text(
                    'Failed to load file',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w500,
                      color: Colors.grey,
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Please try again or go back',
                    style: TextStyle(color: Colors.grey),
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton(
                    onPressed: loadFile,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.deepPurple,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            )
          : HtmlElementView(viewType: viewId),
    );
  }
}
