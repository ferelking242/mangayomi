import 'dart:async';
import '../javascript_runtime.dart';
import '../js_eval_result.dart';

export 'ffi.dart' show JSEvalFlag, JSRef;

class QuickJsRuntime2 extends JavascriptRuntime {
  QuickJsRuntime2({int? stackSize});

  @override
  void dispose() {}

  @override
  JsEvalResult evaluate(String code, {String? sourceUrl}) {
    return JsEvalResult('', null);
  }

  @override
  Future<JsEvalResult> evaluateAsync(String code, {String? sourceUrl}) async {
    return JsEvalResult('', null);
  }

  @override
  JsEvalResult callFunction(dynamic fn, dynamic obj) {
    return JsEvalResult('', null);
  }

  @override
  T? convertValue<T>(JsEvalResult jsValue) => null;

  @override
  String jsonStringify(JsEvalResult jsValue) => '';

  @override
  bool setupBridge(String channelName, void Function(dynamic args) fn) => false;

  @override
  String getEngineInstanceId() => 'web-stub';

  @override
  void setInspectable(bool inspectable) {}

  @override
  int executePendingJob() => 0;

  @override
  void initChannelFunctions() {}
}
