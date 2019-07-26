
;(function() {
  function detect() {
    var nodeVersion = getNodeVersion();
    if (nodeVersion) {
      return nodeVersion;
    } else if (typeof navigator !== 'undefined') {
      return parseUserAgent(navigator.userAgent);
    }

    return null;
  }

  function detectOS(userAgentString) {
    var rules = getOperatingSystemRules();
    var detected = [];

    for(var i = 0; i < rules.length; i++) {
      if (rules[i].rule && rules[i].rule.test(userAgentString)) {
        detected.push(rules[i]);
      }
    }

    return detected[0] ? detected[0].name : null;
  }

  function getNodeVersion() {
    var isNode = typeof navigator === 'undefined' && typeof process !== 'undefined';
    return isNode ? {
      name: 'node',
      version: process.version.slice(1),
      os: require('os').type().toLowerCase()
    } : null;
  }

  function parseUserAgent(userAgentString) {
    var browsers = getBrowserRules();
    if (!userAgentString) {
      return null;
    }

    var detectedList = [];

    for (var i = 0; i < browsers.length; i++) {
      var match = browsers[i].rule.exec(userAgentString);
      var version = match && match[1].split(/[._]/).slice(0,3);

      if (version && version.length < 3) {
        version = version.concat(version.length == 1 ? [0, 0] : [0]);
      }

      if (match) {
        detectedList.push({
          name: browsers[i].name,
          version: version.join('.')
        })
      }
    }

    var detected = detectedList[0] || null;

    if (detected) {
      detected.os = detectOS(userAgentString);
    }

    if (/alexa|bot|crawl(er|ing)|facebookexternalhit|feedburner|google web preview|nagios|postrank|pingdom|slurp|spider|yahoo!|yandex/i.test(userAgentString)) {
      detected = detected || {};
      detected.bot = true;
    }
    
    return detected;
  }

  function getBrowserRules() {
    return buildRules([
      [ 'aol', /AOLShield\/([0-9\._]+)/ ],
      [ 'Edge', /Edge\/([0-9\._]+)/ ],
      [ 'yandexbrowser', /YaBrowser\/([0-9\._]+)/ ],
      [ 'vivaldi', /Vivaldi\/([0-9\.]+)/ ],
      [ 'kakaotalk', /KAKAOTALK\s([0-9\.]+)/ ],
      [ 'samsung', /SamsungBrowser\/([0-9\.]+)/ ],
      [ 'Chrome', /(?!Chrom.*OPR)Chrom(?:e|ium)\/([0-9\.]+)(:?\s|$)/ ],
      [ 'Phantomjs', /PhantomJS\/([0-9\.]+)(:?\s|$)/ ],
      [ 'crios', /CriOS\/([0-9\.]+)(:?\s|$)/ ],
      [ 'Firefox', /Firefox\/([0-9\.]+)(?:\s|$)/ ],
      [ 'fxios', /FxiOS\/([0-9\.]+)/ ],
      [ 'Opera', /Opera\/([0-9\.]+)(?:\s|$)/ ],
      [ 'Opera', /OPR\/([0-9\.]+)(:?\s|$)$/ ],
      [ 'IE', /Trident\/7\.0.*rv\:([0-9\.]+).*\).*Gecko$/ ],
      [ 'IE', /MSIE\s([0-9\.]+);.*Trident\/[4-7].0/ ],
      [ 'IE', /MSIE\s(7\.0)/ ],
      [ 'bb10', /BB10;\sTouch.*Version\/([0-9\.]+)/ ],
      [ 'android', /Android\s([0-9\.]+)/ ],
      [ 'ios', /Version\/([0-9\._]+).*Mobile.*Safari.*/ ],
      [ 'Safari', /Version\/([0-9\._]+).*Safari/ ],
      [ 'Facebook', /FBAV\/([0-9\.]+)/],
      [ 'Instagram', /Instagram\ ([0-9\.]+)/]
    ]);
  }

  function getOperatingSystemRules() {
    return buildRules([
      [ 'iOS', /iP(hone|od|ad)/ ],
      [ 'Android OS', /Android/ ],
      [ 'BlackBerry OS', /BlackBerry|BB10/ ],
      [ 'Windows Mobile', /IEMobile/ ],
      [ 'Amazon OS', /Kindle/ ],
      [ 'Windows 3.11', /Win16/ ],
      [ 'Windows 95', /(Windows 95)|(Win95)|(Windows_95)/ ],
      [ 'Windows 98', /(Windows 98)|(Win98)/ ],
      [ 'Windows 2000', /(Windows NT 5.0)|(Windows 2000)/ ],
      [ 'Windows XP', /(Windows NT 5.1)|(Windows XP)/ ],
      [ 'Windows Server 2003', /(Windows NT 5.2)/ ],
      [ 'Windows Vista', /(Windows NT 6.0)/ ],
      [ 'Windows 7', /(Windows NT 6.1)/ ],
      [ 'Windows 8', /(Windows NT 6.2)/ ],
      [ 'Windows 8.1', /(Windows NT 6.3)/ ],
      [ 'Windows 10', /(Windows NT 10.0)/ ],
      [ 'Windows ME', /Windows ME/ ],
      [ 'Linux', /OpenBSD/ ],
      [ 'Sun OS', /SunOS/ ],
      [ 'Linux', /(Linux)|(X11)/ ],
      [ 'Mac OS', /(Mac_PowerPC)|(Macintosh)/ ],
      [ 'QNX', /QNX/ ],
      [ 'BeOS', /BeOS/ ],
      [ 'OS/2', /OS\/2/ ],
      [ 'Search Bot', /(nuhk)|(Googlebot)|(Yammybot)|(Openbot)|(Slurp)|(MSNBot)|(Ask Jeeves\/Teoma)|(ia_archiver)/ ]
    ]);
  }

  function buildRules(ruleTuples) {
    for (var i = 0; i < ruleTuples.length; i++) {
      ruleTuples[i] = {
        name: ruleTuples[i][0], 
        rule: ruleTuples[i][1] 
      };
    }
    return ruleTuples;
  }

  window.browser = {
    detect: detect,
    detectOS: detectOS,
    getNodeVersion: getNodeVersion,
    parseUserAgent: parseUserAgent
  };
})();
