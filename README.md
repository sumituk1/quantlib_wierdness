About
=====


Input Messages
==============

Market Data Snapshot / Quote Messages
-------------------------------------

```{
  "marketDataSnapshotFullRefreshList": [
    {
      "securityId": "CUSIP",
      "symbol": "912810RB6",
      "timestamp": 1485941760000,
      "marketDataEntryList": [
        {
          "entryId": "entryId101",
          "entryType": "BID",
          "entryPx": "1.12445",
          "currencyCode": "USD",
          "settlementCurrencyCode": "USD",
          "entrySize": "1000000",
          "quoteEntryId": "quoteEntryId101"
        },
        {
          "entryId": "entryId102",
          "entryType": "MID",
          "entryPx": "1.12345",
          "currencyCode": "USD",
          "settlementCurrencyCode": "USD",
          "entrySize": "1000000",
          "quoteEntryId": "quoteEntryId102"
        },
        {
          "entryId": "entryId103",
          "entryType": "OFFER",
          "entryPx": "1.12445",
          "currencyCode": "USD",
          "settlementCurrencyCode": "USD",
          "entrySize": "1000000",
          "quoteEntryId": "quoteEntryId103"
        },
        {
          "entryId": "entryId201",
          "entryType": "BID",
          "entryPx": "1.12445",
          "currencyCode": "USD",
          "settlementCurrencyCode": "USD",
          "entrySize": "1000000",
          "quoteEntryId": "quoteEntryId201"
        },
        {
          "entryId": "entryId202",
          "entryType": "MID",
          "entryPx": "1.12345",
          "currencyCode": "USD",
          "settlementCurrencyCode": "USD",
          "entrySize": "1000000",
          "quoteEntryId": "quoteEntryId202"
        },
        {
          "entryId": "entryId203",
          "entryType": "OFFER",
          "entryPx": "1.12445",
          "currencyCode": "USD",
          "settlementCurrencyCode": "USD",
          "entrySize": "1000000",
          "quoteEntryId": "quoteEntryId203"
        }
      ]
    }
  ]
}```

Mosaic Negoitation Bundle - Has the Trade Information
-----------------------------------------------------

This is going to change to add some 3 or 4 missing fields

```{
  "negotiationBundleFactItem": {
    "dateDimensionItem": {
      "localDate": "2016-09-02",
      "dateTimeEpochUTC": 17046
    },
    "timeDimensionItem": {
      "hour": 13,
      "minute": 14,
      "second": 15
    },
    "zoneDimensionItem": {
      "zoneId": "Europe\/London",
      "description": "Europe\/London",
      "countryDimensionItem": {
        "name": "United Kingdom",
        "isoCode": "UK",
        "region": "EMEA",
        "subRegion": "Europe"
      }
    },
    "timestamp": 1490698946950,
    "negotiationId": "8479e937-f600-4f9b-bb20-71860607f631",
    "venueDimensionItem": {
      "name": "BBGUST",
      "operatingMic": "op",
      "segmentMic": "seg",
      "status": "ACTIVE",
      "countryDimensionItem": {
        "name": "United Kingdom",
        "isoCode": "UK",
        "region": "EMEA",
        "subRegion": "Europe"
      }
    },
    "dealerEntityDimensionItem": {
      "effectiveDateEpoch": 123456,
      "lei": "ABC",
      "legalName": "ABC Industries",
      "industryDimensionItem": {
        "hierarchicalCode": "dummyHierarchicalCode",
        "economicSector": "dummyEconomicSector",
        "businessSector": "dummyBusinessSector",
        "industryGroup": "dummyIndustryGroup",
        "industry": "dummyIndustry",
        "activity": "dummyActivity",
        "description": "dummyDescription"
      },
      "countryDimensionItem": {
        "name": "United Kingdom",
        "isoCode": "UK",
        "region": "EMEA",
        "subRegion": "Europe"
      }
    },
    "dealerTraderDimensionItem": {
      "effectiveDateEpoch": 123456,
      "id": "trader1",
      "name": "John Smith"
    },
    "dealerSalespersonDimensionItem": {
      "effectiveDateEpoch": 123456,
      "id": "salesperson1",
      "name": "Jack Jones"
    },
    "clientEntityDimensionItem": {
      "effectiveDateEpoch": 123456,
      "lei": "XYZ",
      "legalName": "XYZ Industries",
      "industryDimensionItem": {
        "hierarchicalCode": "dummyHierarchicalCode",
        "economicSector": "dummyEconomicSector",
        "businessSector": "dummyBusinessSector",
        "industryGroup": "dummyIndustryGroup",
        "industry": "dummyIndustry",
        "activity": "dummyActivity",
        "description": "dummyDescription"
      },
      "countryDimensionItem": {
        "name": "United Kingdom",
        "isoCode": "UK",
        "region": "EMEA",
        "subRegion": "Europe"
      }
    },
    "clientTraderDimensionItem": {
      "effectiveDateEpoch": 123456,
      "id": "trader2",
      "name": "James Simpson"
    },
    "clientPricingGroupDimensionItem": {
      "effectiveDateEpoch": 123456,
      "group": "GROUP_1",
      "name": "Tier1"
    },
    "negotiationOutcomeDimensionItem": {
      "negotiationOutcome": "Traded",
      "description": "whatever"
    },
    "negotiationOutcomeDetailDimensionItem": {
      "negotiationOutcomeDetail": "No Quote",
      "description": "no quote"
    },
    "negotiationModelTypeDimensionItem": {
      "negotiationModelType": "Request Dealer Last Look",
      "description": "rfq"
    },
    "quoteTypeDimensionItem": {
      "quoteType": "One-Way",
      "description": "one way"
    },
    "negotiationBundleFactItemLegs": [
      {
        "instrumentDimensionItem": {
          "effectiveDateEpoch": 16936,
          "name": "TBILL",
          "currencyDimensionItem": {
            "name": "US Dollar",
            "isoCode": "USD"
          },
          "primaryId": "TWEB-12345",
          "primaryIdType": "ISIN",
          "productDimensionItem": {
            "cfiCode": "cfi",
            "categoryCode": "cat1",
            "categoryName": "Category 1",
            "groupName": "Group 1",
            "groupCode": "grp1",
            "firstAttributeLongName": "1st long",
            "firstAttributeShortName": "1st short",
            "firstAttributeCode": "fa1",
            "firstAttributeDescription": "First attribute",
            "secondAttributeLongName": "2nd long",
            "secondAttributeShortName": "2nd short",
            "secondAttributeCode": "fa2",
            "secondAttributeDescription": "Second attribute",
            "thirdAttributeLongName": "3rd long",
            "thirdAttributeShortName": "3rd short",
            "thirdAttributeCode": "fa3",
            "thirdAttributeDescription": "Third attribute",
            "fourthAttributeLongName": "4th long",
            "fourthAttributeShortName": "4th short",
            "fourthAttributeCode": "fa4",
            "fourthAttributeDescription": "Fourth attribute"
          },
          "monthYear": "01\/12",
          "maturityDate": "10\/01\/2020",
          "maturityTime": "00:00",
          "couponRate": 2.5,
          "couponPeriod": 1,
          "couponUnit": "unit",
          "couponDayCount": "1",
          "issueDate": "10\/01\/2001",
          "issuer": "Bank",
          "issuerCountryDimensionItem": {
            "name": "United Kingdom",
            "isoCode": "UK",
            "region": "EMEA",
            "subRegion": "Europe"
          },
          "industryDimensionItem": {
            "hierarchicalCode": "dummyHierarchicalCode",
            "economicSector": "dummyEconomicSector",
            "businessSector": "dummyBusinessSector",
            "industryGroup": "dummyIndustryGroup",
            "industry": "dummyIndustry",
            "activity": "dummyActivity",
            "description": "dummyDescription"
          }
        },
        "cashflowDirectionDimensionItem": {
          "cashflowDirection": "+",
          "description": "description"
        },
        "baseCurrencyDimensionItem": {
          "name": "US Dollar",
          "isoCode": "USD"
        },
        "currencyDimensionItem": {
          "name": "US Dollar",
          "isoCode": "USD"
        },
        "tenor": 123,
        "baseQuantity": 10000,
        "quantity": 20000,
        "dv01": 30000,
        "quantityDv01": 40000,
        "baseQuantityDv01": 50000,
        "modifiedDuration": 12.34,
        "macaulayDuration": 56.78,
        "tradePrice": 1.23,
        "tradeYield": 4.56,
        "coverPrice": 9.87,
        "coverYield": 6.54,
        "dealerPrice": 1.35,
        "dealerYield": 2.46,
        "negotiationBundleFactItemLegMarkouts": [
          {
            "evaluatedPricingSourceDimensionItem": {
              "evaluatedPricingSource": "Internal",
              "description": "some source"
            },
            "markoutPeriodDimensionItem": {
              "markoutPeriod": {
                "timeUnit": "HOURS",
                "value": 2
              }
            },
            "markoutPrice": {
              "priceType": {
                "priceType": "UNHEDGED_INITIAL_EDGE"
              },
              "value": 0.12
            }
          },
          {
            "evaluatedPricingSourceDimensionItem": {
              "evaluatedPricingSource": "Internal",
              "description": "some source"
            },
            "markoutPeriodDimensionItem": {
              "markoutPeriod": {
                "timeUnit": "HOURS",
                "value": 1
              }
            },
            "markoutPrice": {
              "priceType": {
                "priceType": "UNHEDGED_INITIAL_EDGE"
              },
              "value": 0.13
            }
          },
          {
            "evaluatedPricingSourceDimensionItem": {
              "evaluatedPricingSource": "Internal",
              "description": "some source"
            },
            "markoutPeriodDimensionItem": {
              "markoutPeriod": {
                "timeUnit": "SECONDS",
                "value": 0
              }
            },
            "markoutPrice": {
              "priceType": {
                "priceType": "UNHEDGED_INITIAL_EDGE"
              },
              "value": 0.14
            }
          },
          {
            "evaluatedPricingSourceDimensionItem": {
              "evaluatedPricingSource": "Internal",
              "description": "some source"
            },
            "markoutPeriodDimensionItem": {
              "markoutPeriod": {
                "timeUnit": "HOURS",
                "value": 1
              }
            },
            "markoutPrice": {
              "priceType": {
                "priceType": "UNHEDGED_INITIAL_EDGE"
              },
              "value": 0.13
            }
          }
        ]
      }
    ],
    "numberOfDealers": 1,
    "timeToQuote": 50,
    "timeToTrade": 45
  }
}```

Output Message
