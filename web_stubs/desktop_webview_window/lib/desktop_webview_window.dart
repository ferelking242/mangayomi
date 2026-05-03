import 'dart:async';
import 'package:flutter/material.dart';

bool runWebViewTitleBarWidget(List<String> args) => false;

class WebViewEnvironmentSettings {
  final String? userDataFolder;
  const WebViewEnvironmentSettings({this.userDataFolder});
}

class WebViewEnvironment {
  static Future<String?> getAvailableVersion() async => null;
  static Future<WebViewEnvironment> create({
    WebViewEnvironmentSettings? settings,
  }) async => WebViewEnvironment._();
  WebViewEnvironment._();
}

class Cookie {
  final String name;
  final String value;
  const Cookie(this.name, this.value);
}

class _WebviewOnClose {
  Future<void> whenComplete(void Function() fn) async {}
}

class Webview {
  final _WebviewOnClose onClose = _WebviewOnClose();

  Future<void> close() async {}
  Future<List<Cookie>> getAllCookies() async => [];
  Future<String?> evaluateJavaScript(String script) async => null;
  void addScriptToExecuteOnDocumentCreated(String script) {}
  void setApplicationNameForUserAgent(String name) {}
  void launch(String url) {}
  void setBrightness(Brightness brightness) {}
  void setNavigationDelegate({
    void Function(String url)? onPageStarted,
    void Function(String url)? onPageFinished,
    bool Function(String url)? onNavigationRequest,
  }) {}
}

class WebviewWindow {
  static Future<Webview> create() async => Webview();
}
