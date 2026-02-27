import 'package:flutter/material.dart';

enum AppRole { farmer, distributor, retailer, consumer }

extension AppRoleX on AppRole {
  String get title {
    switch (this) {
      case AppRole.farmer:
        return 'Farmer';
      case AppRole.distributor:
        return 'Distributor';
      case AppRole.retailer:
        return 'Retailer';
      case AppRole.consumer:
        return 'Consumer';
    }
  }

  IconData get icon {
    switch (this) {
      case AppRole.farmer:
        return Icons.agriculture_rounded;
      case AppRole.distributor:
        return Icons.local_shipping_rounded;
      case AppRole.retailer:
        return Icons.storefront_rounded;
      case AppRole.consumer:
        return Icons.qr_code_scanner_rounded;
    }
  }
}

AppRole appRoleFromBackend(String value) {
  switch (value.toLowerCase()) {
    case 'farmer':
      return AppRole.farmer;
    case 'distributor':
      return AppRole.distributor;
    case 'retailer':
      return AppRole.retailer;
    case 'consumer':
      return AppRole.consumer;
    default:
      throw ArgumentError('Unsupported role: $value');
  }
}

class AuthSession {
  const AuthSession({
    required this.userId,
    required this.name,
    required this.phone,
    required this.role,
    required this.walletAddress,
    required this.accessToken,
    required this.refreshToken,
    required this.isVerified,
  });

  final String userId;
  final String name;
  final String phone;
  final AppRole role;
  final String walletAddress;
  final String accessToken;
  final String refreshToken;
  final bool isVerified;

  factory AuthSession.fromBackendJson(Map<String, dynamic> json) {
    final user = json['user'] as Map<String, dynamic>;
    return AuthSession(
      userId: (user['id'] ?? '').toString(),
      name: (user['name'] ?? '').toString(),
      phone: (user['phone'] ?? '').toString(),
      role: appRoleFromBackend((user['role'] ?? '').toString()),
      walletAddress: (user['wallet_address'] ?? '').toString(),
      accessToken: (json['access_token'] ?? '').toString(),
      refreshToken: (json['refresh_token'] ?? '').toString(),
      isVerified: user['is_verified'] == true,
    );
  }
}

class DashboardBatchItem {
  const DashboardBatchItem({
    required this.id,
    required this.batchCode,
    required this.cropType,
    required this.quantity,
    required this.status,
  });

  final String id;
  final String batchCode;
  final String cropType;
  final String quantity;
  final String status;

  factory DashboardBatchItem.fromJson(Map<String, dynamic> json) {
    return DashboardBatchItem(
      id: (json['id'] ?? '').toString(),
      batchCode: (json['batch_code'] ?? '').toString(),
      cropType: (json['crop_type'] ?? '').toString(),
      quantity: (json['quantity'] ?? '').toString(),
      status: (json['status'] ?? '').toString(),
    );
  }
}

class DashboardInventoryItem {
  const DashboardInventoryItem({
    required this.name,
    required this.demandSignal,
    required this.expiryHint,
  });

  final String name;
  final String demandSignal;
  final String expiryHint;

  factory DashboardInventoryItem.fromJson(Map<String, dynamic> json) {
    return DashboardInventoryItem(
      name: (json['name'] ?? '').toString(),
      demandSignal: (json['demand_signal'] ?? '').toString(),
      expiryHint: (json['expiry_hint'] ?? '').toString(),
    );
  }
}

class DashboardPayload {
  const DashboardPayload({
    required this.role,
    required this.greetingName,
    required this.summaryTitle,
    required this.summarySubtitle,
    required this.weatherText,
    required this.pricePredictionText,
    required this.freshnessScore,
    required this.trustScore,
    required this.activeBatchesCount,
    required this.pendingTransfersCount,
    required this.recentBatches,
    required this.inventoryItems,
    required this.alerts,
    required this.orders,
    required this.recommendation,
  });

  final AppRole role;
  final String greetingName;
  final String summaryTitle;
  final String summarySubtitle;
  final String weatherText;
  final String pricePredictionText;
  final int freshnessScore;
  final int trustScore;
  final int activeBatchesCount;
  final int pendingTransfersCount;
  final List<DashboardBatchItem> recentBatches;
  final List<DashboardInventoryItem> inventoryItems;
  final List<String> alerts;
  final List<String> orders;
  final String recommendation;

  factory DashboardPayload.fromJson(Map<String, dynamic> json) {
    final roleRaw = (json['role'] ?? '').toString();
    final batches = (json['recent_batches'] as List<dynamic>? ?? const [])
        .whereType<Map<String, dynamic>>()
        .map(DashboardBatchItem.fromJson)
        .toList();
    final inventory = (json['inventory_items'] as List<dynamic>? ?? const [])
        .whereType<Map<String, dynamic>>()
        .map(DashboardInventoryItem.fromJson)
        .toList();

    return DashboardPayload(
      role: appRoleFromBackend(roleRaw),
      greetingName: (json['greeting_name'] ?? '').toString(),
      summaryTitle: (json['summary_title'] ?? '').toString(),
      summarySubtitle: (json['summary_subtitle'] ?? '').toString(),
      weatherText: (json['weather_text'] ?? '').toString(),
      pricePredictionText: (json['price_prediction_text'] ?? '').toString(),
      freshnessScore: (json['freshness_score'] as num?)?.toInt() ?? 0,
      trustScore: (json['trust_score'] as num?)?.toInt() ?? 0,
      activeBatchesCount: (json['active_batches_count'] as num?)?.toInt() ?? 0,
      pendingTransfersCount:
          (json['pending_transfers_count'] as num?)?.toInt() ?? 0,
      recentBatches: batches,
      inventoryItems: inventory,
      alerts: (json['alerts'] as List<dynamic>? ?? const [])
          .map((item) => item.toString())
          .toList(),
      orders: (json['orders'] as List<dynamic>? ?? const [])
          .map((item) => item.toString())
          .toList(),
      recommendation: (json['recommendation'] ?? '').toString(),
    );
  }
}
