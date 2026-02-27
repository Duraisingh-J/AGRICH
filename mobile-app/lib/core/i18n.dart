import 'package:flutter/material.dart';

class I18nController extends ChangeNotifier {
  String _lang = 'en';

  String get lang => _lang;

  static const Map<String, Map<String, String>> _localized = {
    'en': {
      'tagline': 'Trust in Every Harvest',
      'scan': 'Scan',
      'explore': 'Explore',
      'my_orders': 'My Orders',
      'profile': 'Profile',
      'dashboard': 'Dashboard',
      'insights': 'Insights',
      'language': 'Language',
      'logout': 'Logout',
      'verification_status': 'Verification Status',
      'trust_score': 'Trust Score',
      'wallet_address': 'Wallet Address',
      'dark_mode': 'Dark Mode',
      'recommended_action': 'Recommended Action',
    },
    'hi': {
      'tagline': 'हर फसल में भरोसा',
      'scan': 'स्कैन',
      'explore': 'एक्सप्लोर',
      'my_orders': 'मेरे ऑर्डर',
      'profile': 'प्रोफ़ाइल',
      'dashboard': 'डैशबोर्ड',
      'insights': 'इनसाइट्स',
      'language': 'भाषा',
      'logout': 'लॉगआउट',
      'verification_status': 'सत्यापन स्थिति',
      'trust_score': 'ट्रस्ट स्कोर',
      'wallet_address': 'वॉलेट पता',
      'dark_mode': 'डार्क मोड',
      'recommended_action': 'सुझाया गया एक्शन',
    },
    'ta': {
      'tagline': 'ஒவ்வொரு அறுவடையிலும் நம்பிக்கை',
      'scan': 'ஸ்கேன்',
      'explore': 'ஆராய்வு',
      'my_orders': 'என் ஆர்டர்கள்',
      'profile': 'சுயவிவரம்',
      'dashboard': 'டாஷ்போர்டு',
      'insights': 'இன்சைட்ஸ்',
      'language': 'மொழி',
      'logout': 'வெளியேறு',
      'verification_status': 'சரிபார்ப்பு நிலை',
      'trust_score': 'நம்பகத்தன்மை மதிப்பு',
      'wallet_address': 'வாலெட் முகவரி',
      'dark_mode': 'இருண்ட தீம்',
      'recommended_action': 'பரிந்துரைக்கப்பட்ட செயல்',
    },
  };

  String t(String key) =>
      _localized[_lang]?[key] ?? _localized['en']![key] ?? key;

  Future<void> setLanguage(String code) async {
    _lang = code;
    notifyListeners();
    await _requestApiFallbackIfKeyMissing();
  }

  Future<void> _requestApiFallbackIfKeyMissing() async {
    await Future<void>.delayed(const Duration(milliseconds: 180));
  }
}
