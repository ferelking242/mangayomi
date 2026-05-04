import 'dart:async';

class JsEvalResult {
  final String stringResult;
  final dynamic rawResult;
  final bool isPromise;
  final bool isError;

  JsEvalResult(this.stringResult, this.rawResult,
      {this.isError = false, this.isPromise = false});

  @override
  String toString() => stringResult;
}

abstract class JavascriptRuntime {
  static bool debugEnabled = false;

  Map<String, dynamic> localContext = {};
  Map<String, dynamic> dartContext = {};

  JavascriptRuntime init() => this;
  void dispose();
  JsEvalResult evaluate(String code, {String? sourceUrl});
  Future<JsEvalResult> evaluateAsync(String code, {String? sourceUrl});
  JsEvalResult callFunction(dynamic fn, dynamic obj);
  T? convertValue<T>(JsEvalResult jsValue);
  String jsonStringify(JsEvalResult jsValue);
  bool setupBridge(String channelName, void Function(dynamic args) fn);
  String getEngineInstanceId();
  void setInspectable(bool inspectable);
  int executePendingJob();
  void initChannelFunctions();
  void onMessage(String channelName, dynamic Function(dynamic args) fn) {
    setupBridge(channelName, fn);
  }
}

class _QuickJsStub extends JavascriptRuntime {
  @override void dispose() {}
  @override JsEvalResult evaluate(String code, {String? sourceUrl}) => JsEvalResult('', null);
  @override Future<JsEvalResult> evaluateAsync(String code, {String? sourceUrl}) async => JsEvalResult('', null);
  @override JsEvalResult callFunction(dynamic fn, dynamic obj) => JsEvalResult('', null);
  @override T? convertValue<T>(JsEvalResult jsValue) => null;
  @override String jsonStringify(JsEvalResult jsValue) => '';
  @override bool setupBridge(String channelName, void Function(dynamic args) fn) => false;
  @override String getEngineInstanceId() => 'web-stub';
  @override void setInspectable(bool inspectable) {}
  @override int executePendingJob() => 0;
  @override void initChannelFunctions() {}
}

JavascriptRuntime getJavascriptRuntime({Map<String, dynamic>? extraArgs = const {}}) {
  return _QuickJsStub();
}

extension HandlePromises on JavascriptRuntime {
  void enableHandlePromises() {}
  Future<JsEvalResult> handlePromise(JsEvalResult value, {Duration? timeout}) async => value;
}
