// ignore_for_file: non_constant_identifier_names

class Platform {
  static bool get isAndroid => false;
  static bool get isIOS => false;
  static bool get isLinux => false;
  static bool get isMacOS => false;
  static bool get isWindows => false;
  static bool get isFuchsia => false;
  static String get operatingSystem => 'web';
  static String get operatingSystemVersion => '';
  static String get localHostname => '';
  static int get numberOfProcessors => 1;
  static String get pathSeparator => '/';
  static Map<String, String> get environment => {};
  static String get executable => '';
  static List<String> get executableArguments => [];
  static String get resolvedExecutable => '';
  static Uri get script => Uri();
  static String? get packageConfig => null;
  static String get localeName => 'en_US';
}

void exit(int code) {
  throw UnsupportedError('exit() is not supported on web');
}

class Stdin {}
class Stdout {}

class Directory {
  final String path;
  const Directory(this.path);
  static Future<Directory> get systemTemp async => const Directory('/tmp');
  Future<bool> exists() async => false;
  Future<Directory> create({bool recursive = false}) async => this;
  Stream<dynamic> list({bool recursive = false, bool followLinks = true}) => const Stream.empty();
}

class File {
  final String path;
  const File(this.path);
  Future<bool> exists() async => false;
  Future<String> readAsString({dynamic encoding}) async => '';
  Future<File> writeAsString(String contents, {dynamic mode, dynamic encoding, bool flush = false}) async => this;
  Future<File> writeAsBytes(List<int> bytes, {dynamic mode, bool flush = false}) async => this;
  Future<List<int>> readAsBytes() async => [];
}

class ProcessSignal {
  static final sigterm = ProcessSignal._('SIGTERM');
  static final sigint = ProcessSignal._('SIGINT');
  final String _name;
  ProcessSignal._(this._name);
  Stream<ProcessSignal> watch() => const Stream.empty();
}

class InternetAddress {
  final String address;
  const InternetAddress(this.address);
  static final loopbackIPv4 = const InternetAddress('127.0.0.1');
  static final anyIPv4 = const InternetAddress('0.0.0.0');
}

class HttpOverrides {
  static HttpOverrides? global;
}
