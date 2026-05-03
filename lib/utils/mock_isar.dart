// ignore_for_file: public_member_api_docs, invalid_use_of_protected_member

import 'dart:typed_data';

import 'package:isar_community/isar.dart';
import 'package:meta/meta.dart';

class MockQuery<T> extends Query<T> {
  @override
  final Isar isar;

  MockQuery(this.isar);

  @override
  Future<T?> findFirst() => Future.value(null);

  @override
  T? findFirstSync() => null;

  @override
  Future<List<T>> findAll() => Future.value([]);

  @override
  List<T> findAllSync() => [];

  @override
  @protected
  Future<R?> aggregate<R>(AggregationOp op) {
    if (op == AggregationOp.count) return Future.value(0 as R?);
    if (op == AggregationOp.isEmpty) return Future.value(1 as R?);
    return Future.value(null);
  }

  @override
  @protected
  R? aggregateSync<R>(AggregationOp op) {
    if (op == AggregationOp.count) return 0 as R?;
    if (op == AggregationOp.isEmpty) return 1 as R?;
    return null;
  }

  @override
  Future<bool> deleteFirst() => Future.value(false);

  @override
  bool deleteFirstSync() => false;

  @override
  Future<int> deleteAll() => Future.value(0);

  @override
  int deleteAllSync() => 0;

  @override
  Stream<List<T>> watch({bool fireImmediately = false}) => const Stream.empty();

  @override
  Stream<void> watchLazy({bool fireImmediately = false}) =>
      const Stream.empty();

  @override
  Future<R> exportJsonRaw<R>(R Function(Uint8List) callback) =>
      Future.value(callback(Uint8List(0)));

  @override
  R exportJsonRawSync<R>(R Function(Uint8List) callback) =>
      callback(Uint8List(0));
}

class MockIsarCollection<OBJ> extends IsarCollection<OBJ> {
  final MockIsar _mockIsar;

  MockIsarCollection(this._mockIsar);

  @override
  Isar get isar => _mockIsar;

  @override
  String get name => 'mock';

  @override
  CollectionSchema<OBJ> get schema =>
      throw UnsupportedError('Web mock: schema not available');

  @override
  Future<List<OBJ?>> getAll(List<int> ids) =>
      Future.value(List.filled(ids.length, null));

  @override
  List<OBJ?> getAllSync(List<int> ids) => List.filled(ids.length, null);

  @override
  Future<List<OBJ?>> getAllByIndex(
          String indexName, List<List<Object?>> keys) =>
      Future.value(List.filled(keys.length, null));

  @override
  List<OBJ?> getAllByIndexSync(String indexName, List<List<Object?>> keys) =>
      List.filled(keys.length, null);

  @override
  Future<List<int>> putAll(List<OBJ> objects) =>
      Future.value(List.filled(objects.length, 0));

  @override
  List<int> putAllSync(List<OBJ> objects, {bool saveLinks = true}) =>
      List.filled(objects.length, 0);

  @override
  Future<List<int>> putAllByIndex(String indexName, List<OBJ> objects) =>
      Future.value(List.filled(objects.length, 0));

  @override
  List<int> putAllByIndexSync(String indexName, List<OBJ> objects,
          {bool saveLinks = true}) =>
      List.filled(objects.length, 0);

  @override
  Future<int> deleteAll(List<int> ids) => Future.value(0);

  @override
  int deleteAllSync(List<int> ids) => 0;

  @override
  Future<int> deleteAllByIndex(String indexName, List<List<Object?>> keys) =>
      Future.value(0);

  @override
  int deleteAllByIndexSync(String indexName, List<List<Object?>> keys) => 0;

  @override
  Future<void> clear() => Future.value();

  @override
  void clearSync() {}

  @override
  Future<void> importJsonRaw(Uint8List jsonBytes) => Future.value();

  @override
  void importJsonRawSync(Uint8List jsonBytes) {}

  @override
  Future<void> importJson(List<Map<String, dynamic>> json) => Future.value();

  @override
  void importJsonSync(List<Map<String, dynamic>> json) {}

  @override
  Query<R> buildQuery<R>({
    List<WhereClause> whereClauses = const [],
    bool whereDistinct = false,
    Sort whereSort = Sort.asc,
    FilterOperation? filter,
    List<SortProperty> sortBy = const [],
    List<DistinctProperty> distinctBy = const [],
    int? offset,
    int? limit,
    String? property,
  }) =>
      MockQuery<R>(_mockIsar);

  @override
  Future<int> count() => Future.value(0);

  @override
  int countSync() => 0;

  @override
  Future<int> getSize(
          {bool includeIndexes = false, bool includeLinks = false}) =>
      Future.value(0);

  @override
  int getSizeSync({bool includeIndexes = false, bool includeLinks = false}) =>
      0;

  @override
  Stream<void> watchLazy({bool fireImmediately = false}) =>
      const Stream.empty();

  @override
  Stream<OBJ?> watchObject(int id, {bool fireImmediately = false}) =>
      Stream.value(null);

  @override
  Stream<void> watchObjectLazy(int id, {bool fireImmediately = false}) =>
      const Stream.empty();

  @override
  Future<void> verify(List<OBJ> objects) => Future.value();

  @override
  Future<void> verifyLink(
          String linkName, List<int> sourceIds, List<int> targetIds) =>
      Future.value();
}

class MockIsar extends Isar {
  final Map<Type, IsarCollection<dynamic>> _mockCollections = {};

  MockIsar() : super('watchtowerDb');

  @override
  String? get directory => null;

  @override
  IsarCollection<T> collection<T>() {
    return _mockCollections.putIfAbsent(T, () => MockIsarCollection<T>(this))
        as IsarCollection<T>;
  }

  @override
  Future<T> txn<T>(Future<T> Function() callback) => callback();

  @override
  T txnSync<T>(T Function() callback) => callback();

  @override
  Future<T> writeTxn<T>(Future<T> Function() callback,
          {bool silent = false}) =>
      callback();

  @override
  T writeTxnSync<T>(T Function() callback, {bool silent = false}) =>
      callback();

  @override
  Future<int> getSize(
          {bool includeIndexes = false, bool includeLinks = false}) =>
      Future.value(0);

  @override
  int getSizeSync({bool includeIndexes = false, bool includeLinks = false}) =>
      0;

  @override
  Future<void> copyToFile(String targetPath) => Future.value();

  @override
  Future<void> verify() => Future.value();
}
