// mobile_html_viewer.dart
// This file is part of the MIR Frontend project.
// It is responsible for displaying HTML content in a WebView or using Flutter HTML package.
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_html/flutter_html.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:webview_flutter/webview_flutter.dart';

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
  String htmlContent = '';
  bool isLoading = true;
  bool hasError = false;
  late WebViewController webViewController;

  @override
  void initState() {
    super.initState();

    if (!kIsWeb) {
      // Initialize only for Android/iOS
      webViewController = WebViewController()
        ..setJavaScriptMode(JavaScriptMode.unrestricted)
        ..setNavigationDelegate(
          NavigationDelegate(
            onPageStarted: (String url) {},
            onPageFinished: (String url) {},
          ),
        );
    }

    loadFile();
  }

  Future<void> loadFile() async {
    try {
      final response = await http.get(
        Uri.parse(
          '${widget.baseUrl}/view/${widget.sessionId}/${widget.fileId}',
        ),
      );

      if (response.statusCode == 200) {
        final injectedHtml = response.body
            .replaceFirst('</head>', """
<script>
  window.MathJax = {
    tex: {inlineMath: [['\$','\$'], ['\\(','\\)']]},
    options: {
      skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre'],
      processHtmlClass: 'mathjax-process',
    }
  };
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" async></script>
</head>
""")
            .replaceFirst('<body', '<body class="mathjax-process"');

        if (!kIsWeb) {
          await webViewController.loadHtmlString(injectedHtml);
        }

        setState(() {
          htmlContent = injectedHtml;
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
      setState(() {
        isLoading = false;
        hasError = true;
      });
    }
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
              setState(() {
                isLoading = true;
                hasError = false;
              });
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
                    onPressed: () {
                      setState(() {
                        isLoading = true;
                        hasError = false;
                      });
                      loadFile();
                    },
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
          : Padding(
              padding: const EdgeInsets.all(16),
              child: kIsWeb
                  ? SingleChildScrollView(child: Html(data: htmlContent))
                  : WebViewWidget(controller: webViewController),
            ),
    );
  }
}
