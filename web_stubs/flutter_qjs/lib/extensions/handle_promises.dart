import 'dart:async';
import '../javascript_runtime.dart';
import '../js_eval_result.dart';

extension HandlePromises on JavascriptRuntime {
  void enableHandlePromises() {}

  Future<JsEvalResult> handlePromise(JsEvalResult value, {Duration? timeout}) async {
    return value;
  }
}
