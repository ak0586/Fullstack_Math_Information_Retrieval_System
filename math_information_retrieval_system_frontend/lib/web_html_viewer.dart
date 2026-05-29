// web_html_viewer.dart
// Web-specific HTML viewer with modern web APIs
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:web/web.dart' as web;
import 'dart:ui_web' as ui_web;
import 'dart:js_interop' as js;

class FileViewerPage extends StatefulWidget {
  final String sessionId;
  final String fileId;
  final String filename;
  final String baseUrl;

  const FileViewerPage({
    required this.sessionId,
    required this.fileId,
    required this.filename,
    required this.baseUrl,
    super.key,
  });

  @override
  _FileViewerPageState createState() => _FileViewerPageState();
}

class _FileViewerPageState extends State<FileViewerPage> {
  bool isLoading = true;
  bool hasError = false;
  String? errorMessage;

  // A unique, stable view ID for this page instance.
  // Using a static counter ensures each FileViewerPage gets a unique ID
  // even if the same file is opened multiple times.
  static int _viewCounter = 0;
  late final String viewId;

  // The iframe element – created once per page instance.
  late final web.HTMLIFrameElement _iframeElement;

  // Track which viewIds have been registered to avoid double-registration.
  static final Set<String> _registeredViewIds = {};

  @override
  void initState() {
    super.initState();
    _viewCounter++;
    viewId = 'html-viewer-${widget.fileId}-$_viewCounter';

    // Create the iframe element once
    _iframeElement = web.HTMLIFrameElement()
      ..style.width = '100%'
      ..style.height = '100%'
      ..style.border = 'none';

    // Register the platform view factory ONCE per viewId
    if (!_registeredViewIds.contains(viewId)) {
      _registeredViewIds.add(viewId);
      ui_web.platformViewRegistry.registerViewFactory(
        viewId,
        (int id) => _iframeElement,
      );
    }

    loadFile();
  }

  Future<void> loadFile() async {
    setState(() {
      isLoading = true;
      hasError = false;
      errorMessage = null;
    });

    try {
      final response = await http.post(
        Uri.parse('${widget.baseUrl}/search'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'query': '__VIEW__:${widget.sessionId}:${widget.fileId}',
        }),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final encodedHtml = data['html'] as String;

        // Decode base64 → UTF-8 HTML string
        final htmlContent = utf8.decode(
          base64.decode(
            encodedHtml.replaceAll('\n', '').replaceAll('\r', '').trim(),
          ),
        );

        // Wrap with MathJax support
        final enhancedHtml = _createEnhancedHtml(htmlContent);

        // Update the already-registered iframe's srcdoc directly.
        // This works because the factory returned the same element instance.
        _iframeElement.srcdoc = enhancedHtml.toJS;

        setState(() {
          isLoading = false;
          hasError = false;
        });
      } else {
        String detail = 'Unknown error';
        try {
          final errData = json.decode(response.body);
          detail = errData['detail'] ?? 'HTTP ${response.statusCode}';
        } catch (_) {
          detail = 'HTTP ${response.statusCode}';
        }
        setState(() {
          isLoading = false;
          hasError = true;
          errorMessage = detail;
        });
      }
    } catch (e) {
      debugPrint('Error loading file: $e');
      setState(() {
        isLoading = false;
        hasError = true;
        errorMessage = e.toString();
      });
    }
  }

  String _createEnhancedHtml(String htmlContent) {
    return '''<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script type="text/javascript" id="MathJax-script" async
      src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/mml-chtml.js">
    </script>
    <style>
      body {
        margin: 10px;
        padding: 5px;
        font-family: sans-serif;
        line-height: 1.6;
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
</html>''';
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
            onPressed: loadFile,
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
                  if (errorMessage != null)
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 24),
                      child: Text(
                        errorMessage!,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          color: Colors.redAccent,
                          fontSize: 13,
                        ),
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
