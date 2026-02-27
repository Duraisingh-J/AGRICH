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
