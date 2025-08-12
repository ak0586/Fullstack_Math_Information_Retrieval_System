// main.dart
// ########

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'dart:io' show Platform;
import 'mobile_html_viewer.dart';
import 'web_html_viewer.dart';

void main() {
  runApp(MathSearchApp());
}

class MathSearchApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Math Search Engine',
      theme: ThemeData(
        primarySwatch: Colors.deepPurple,
        visualDensity: VisualDensity.adaptivePlatformDensity,
        fontFamily: 'Roboto',
      ),
      home: SearchHomePage(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class SearchHomePage extends StatefulWidget {
  @override
  _SearchHomePageState createState() => _SearchHomePageState();
}

class _SearchHomePageState extends State<SearchHomePage>
    with TickerProviderStateMixin {
  final TextEditingController _searchController = TextEditingController();
  late final String baseUrl; // Replace with your API URL
  final ScrollController _scrollController = ScrollController();

  List<SearchResult> searchResults = [];
  bool isLoading = false;
  bool hasSearched = false;
  double timeTaken = 0.0;
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();
    baseUrl = getBaseUrl();
    _animationController = AnimationController(
      duration: Duration(milliseconds: 800),
      vsync: this,
    );
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );
  }

  String getBaseUrl() {
    if (kIsWeb) {
      return 'http://127.0.0.1:8000'; // Web
    } else if (Platform.isAndroid) {
      return 'http://10.0.2.2:8000'; // Android Emulator
    } else {
      return 'http://127.0.0.1:8000'; // iOS Simulator or Desktop
    }
  }

  @override
  void dispose() {
    _animationController.dispose();
    _searchController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  /// Converts normal LaTeX query to JSON-compatible format
  /// - Single slash '/' becomes double slash '//'
  /// - Double slash '//' becomes quadruple slash '////'
  String convertLatexToJsonCompatible(String query) {
    // First replace double slashes with a temporary placeholder to avoid conflicts
    String result = query.replaceAll('//', '___DOUBLE_SLASH___');

    // Replace single slashes with double slashes
    result = result.replaceAll('/', '//');

    // Replace the temporary placeholder with quadruple slashes
    result = result.replaceAll('___DOUBLE_SLASH___', '////');

    return result;
  }

  Future<void> performSearch() async {
    if (_searchController.text.trim().isEmpty) {
      _showSnackBar('Please enter a search query', Colors.orange);
      return;
    }

    setState(() {
      isLoading = true;
      hasSearched = false;
    });

    try {
      // Convert the user's normal LaTeX query to JSON-compatible format
      String jsonCompatibleQuery = convertLatexToJsonCompatible(
        _searchController.text.trim(),
      );

      final response = await http.post(
        Uri.parse('$baseUrl/search'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'query': jsonCompatibleQuery}),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          timeTaken = data['time_taken_in_second'];
          searchResults = (data['results'] as List)
              .map((item) => SearchResult.fromJson(item))
              .toList();
          hasSearched = true;
        });
        _animationController.forward();
        _showSnackBar(
          'Found ${searchResults.length} results in ${timeTaken.toStringAsFixed(3)}s',
          Colors.green,
        );
      } else if (response.statusCode == 400) {
        final errorData = json.decode(response.body);
        _showSnackBar(errorData['detail'], Colors.red);
      } else {
        _showSnackBar('Search failed. Please try again.', Colors.red);
      }
    } catch (e) {
      _showSnackBar('Network error. Please check your connection.', Colors.red);
    } finally {
      setState(() {
        isLoading = false;
      });
    }
  }

  void _showSnackBar(String message, Color color) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: color,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
    );
  }

  void openFile(String fileId, String filename) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => kIsWeb
            ? WebFileViewerPage(
                fileId: fileId,
                filename: filename,
                baseUrl: baseUrl,
              )
            : FileViewerPage(
                fileId: fileId,
                filename: filename,
                baseUrl: baseUrl,
              ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      resizeToAvoidBottomInset: true, // This helps with keyboard handling
      appBar: AppBar(
        title: Text(
          'Math Search Engine',
          style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white),
        ),
        backgroundColor: Colors.deepPurple,
        elevation: 0,
        centerTitle: true,
      ),
      body: GestureDetector(
        onTap: () => FocusScope.of(
          context,
        ).unfocus(), // Dismiss keyboard when tapping outside
        child: Column(
          children: [
            // Search Header - Make it flexible to shrink when keyboard appears
            Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [Colors.deepPurple, Colors.deepPurple.shade300],
                ),
              ),
              padding: EdgeInsets.fromLTRB(
                20,
                20,
                20,
                10,
              ), // Reduced bottom padding
              child: Column(
                mainAxisSize: MainAxisSize.min, // Take minimum space needed
                children: [
                  // Search Input
                  Container(
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(15),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.1),
                          blurRadius: 10,
                          offset: Offset(0, 5),
                        ),
                      ],
                    ),
                    child: TextField(
                      controller: _searchController,
                      decoration: InputDecoration(
                        hintText: 'Enter mathematical expression or LaTeX...',
                        prefixIcon: Icon(
                          Icons.search,
                          color: Colors.deepPurple,
                        ),
                        border: InputBorder.none,
                        contentPadding: EdgeInsets.symmetric(
                          horizontal: 20,
                          vertical: 15,
                        ),
                      ),
                      onSubmitted: (_) => performSearch(),
                      textInputAction: TextInputAction
                          .search, // Shows search button on keyboard
                    ),
                  ),
                  SizedBox(height: 15),
                  // Search Button
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: isLoading ? null : performSearch,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: Colors.deepPurple,
                        padding: EdgeInsets.symmetric(vertical: 15),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10),
                        ),
                        elevation: 5,
                      ),
                      child: isLoading
                          ? SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                valueColor: AlwaysStoppedAnimation<Color>(
                                  Colors.deepPurple,
                                ),
                              ),
                            )
                          : Text(
                              'Search',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                    ),
                  ),
                ],
              ),
            ),

            // Results Section - Flexible to take remaining space
            Flexible(
              // Changed from Expanded to Flexible
              child: hasSearched
                  ? Column(
                      children: [
                        // Results Header
                        Container(
                          padding: EdgeInsets.all(16),
                          child: Column(
                            children: [
                              Text(
                                'Click on file to view',
                                style: TextStyle(
                                  color: Colors.grey[600],
                                  fontSize: 14,
                                  fontStyle: FontStyle.italic,
                                ),
                              ),
                              SizedBox(height: 8),
                              Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(
                                    Icons.timer,
                                    color: Colors.green,
                                    size: 16,
                                  ),
                                  SizedBox(width: 5),
                                  Text(
                                    '${timeTaken.toStringAsFixed(3)}s • ${searchResults.length} results',
                                    style: TextStyle(
                                      color: Colors.grey[700],
                                      fontSize: 12,
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),

                        // Results List
                        Expanded(
                          child: FadeTransition(
                            opacity: _fadeAnimation,
                            child: searchResults.isEmpty
                                ? Center(
                                    child: Column(
                                      mainAxisAlignment:
                                          MainAxisAlignment.center,
                                      children: [
                                        Icon(
                                          Icons.search_off,
                                          size: 60,
                                          color: Colors.grey[400],
                                        ),
                                        SizedBox(height: 16),
                                        Text(
                                          'No results found',
                                          style: TextStyle(
                                            fontSize: 18,
                                            color: Colors.grey[600],
                                            fontWeight: FontWeight.w500,
                                          ),
                                        ),
                                      ],
                                    ),
                                  )
                                : ListView.builder(
                                    controller: _scrollController,
                                    padding: EdgeInsets.symmetric(
                                      horizontal: 16,
                                    ),
                                    itemCount: searchResults.length,
                                    itemBuilder: (context, index) {
                                      final result = searchResults[index];
                                      return AnimatedContainer(
                                        duration: Duration(
                                          milliseconds: 200 + (index * 50),
                                        ),
                                        curve: Curves.easeOutBack,
                                        child: Card(
                                          margin: EdgeInsets.only(bottom: 12),
                                          elevation: 3,
                                          shape: RoundedRectangleBorder(
                                            borderRadius: BorderRadius.circular(
                                              12,
                                            ),
                                          ),
                                          child: InkWell(
                                            borderRadius: BorderRadius.circular(
                                              12,
                                            ),
                                            onTap: () => openFile(
                                              result.id,
                                              result.filename,
                                            ),
                                            child: Padding(
                                              padding: EdgeInsets.all(16),
                                              child: Row(
                                                children: [
                                                  Container(
                                                    width: 40,
                                                    height: 40,
                                                    decoration: BoxDecoration(
                                                      color: Colors.deepPurple
                                                          .withOpacity(0.1),
                                                      borderRadius:
                                                          BorderRadius.circular(
                                                            8,
                                                          ),
                                                    ),
                                                    child: Center(
                                                      child: Text(
                                                        result.id,
                                                        style: TextStyle(
                                                          color:
                                                              Colors.deepPurple,
                                                          fontWeight:
                                                              FontWeight.bold,
                                                        ),
                                                      ),
                                                    ),
                                                  ),
                                                  SizedBox(width: 16),
                                                  Expanded(
                                                    child: Column(
                                                      crossAxisAlignment:
                                                          CrossAxisAlignment
                                                              .start,
                                                      children: [
                                                        Text(
                                                          result.filename,
                                                          style: TextStyle(
                                                            fontSize: 16,
                                                            fontWeight:
                                                                FontWeight.w500,
                                                            color: Colors
                                                                .grey[800],
                                                          ),
                                                        ),
                                                        SizedBox(height: 4),
                                                        Text(
                                                          'Result #${result.id}',
                                                          style: TextStyle(
                                                            fontSize: 12,
                                                            color: Colors
                                                                .grey[600],
                                                          ),
                                                        ),
                                                      ],
                                                    ),
                                                  ),
                                                  Icon(
                                                    Icons.arrow_forward_ios,
                                                    color: Colors.grey[400],
                                                    size: 16,
                                                  ),
                                                ],
                                              ),
                                            ),
                                          ),
                                        ),
                                      );
                                    },
                                  ),
                          ),
                        ),
                      ],
                    )
                  : Center(
                      child: SingleChildScrollView(
                        // Make the empty state scrollable too
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.calculate_outlined,
                              size: 80,
                              color: Colors.grey[400],
                            ),
                            SizedBox(height: 24),
                            Text(
                              'Search Mathematical Expressions',
                              style: TextStyle(
                                fontSize: 24,
                                fontWeight: FontWeight.bold,
                                color: Colors.grey[700],
                              ),
                            ),
                            SizedBox(height: 12),
                            Text(
                              'Enter LaTeX or mathematical expressions\nto find relevant documents',
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                fontSize: 16,
                                color: Colors.grey[600],
                                height: 1.5,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
            ),
          ],
        ),
      ),
    );
  }
}

class SearchResult {
  final String id;
  final String filename;

  SearchResult({required this.id, required this.filename});

  factory SearchResult.fromJson(Map<String, dynamic> json) {
    return SearchResult(id: json['id'], filename: json['filename']);
  }
}
