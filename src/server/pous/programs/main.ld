PROGRAM main
VAR
	CoolingPumpStatus : bool AT %QX0.0; (* Trạng thái bật tắt máy bơm *)
	CurrentTemp : int AT %MW0 := 0; (* Nhiệt độ hiện tại *)
	MaxLimitTemp : int AT %MW1 := 50; (* Giới hạn tối đa trước khi phải bật máy bơm *)
END_VAR

{
  "name": "main",
  "rungs": [
    {
      "id": "rung_main_c8567ade-943a-4062-8b88-d21c20d95ff3",
      "comment": "",
      "defaultBounds": [
        300,
        100
      ],
      "reactFlowViewport": [
        496,
        174
      ],
      "nodes": [
        {
          "id": "left-rail-rung_main_c8567ade-943a-4062-8b88-d21c20d95ff3",
          "type": "powerRail",
          "position": {
            "x": 0,
            "y": 30
          },
          "height": 40,
          "width": 3,
          "measured": {
            "width": 3,
            "height": 40
          },
          "draggable": false,
          "selectable": false,
          "data": {
            "handles": [
              {
                "glbPosition": {
                  "x": 3,
                  "y": 50
                },
                "relPosition": {
                  "x": 3,
                  "y": 20
                },
                "id": "left-rail",
                "position": "right",
                "type": "source",
                "isConnectable": false,
                "style": {
                  "top": 20,
                  "right": -3
                }
              }
            ],
            "inputHandles": [],
            "outputHandles": [
              {
                "glbPosition": {
                  "x": 3,
                  "y": 50
                },
                "relPosition": {
                  "x": 3,
                  "y": 20
                },
                "id": "left-rail",
                "position": "right",
                "type": "source",
                "isConnectable": false,
                "style": {
                  "top": 20,
                  "right": -3
                }
              }
            ],
            "outputConnector": {
              "glbPosition": {
                "x": 3,
                "y": 50
              },
              "relPosition": {
                "x": 3,
                "y": 20
              },
              "id": "left-rail",
              "position": "right",
              "type": "source",
              "isConnectable": false,
              "style": {
                "top": 20,
                "right": -3
              }
            },
            "numericId": "4689414",
            "variant": "left",
            "variable": {
              "name": ""
            },
            "executionOrder": 0,
            "draggable": false,
            "selectable": false,
            "deletable": false,
            "hasDivergence": false
          }
        },
        {
          "id": "BLOCK_9e0ffea3-93df-4fd7-a930-d6b7a312d96d",
          "type": "block",
          "position": {
            "x": 143,
            "y": 14
          },
          "height": 140,
          "width": 90,
          "measured": {
            "width": 90,
            "height": 140
          },
          "draggable": true,
          "selectable": true,
          "data": {
            "handles": [
              {
                "glbPosition": {
                  "x": 143,
                  "y": 50
                },
                "relPosition": {
                  "x": 0,
                  "y": 36
                },
                "id": "EN",
                "position": "left",
                "type": "target",
                "isConnectable": false,
                "style": {
                  "top": 36,
                  "left": 0
                }
              },
              {
                "glbPosition": {
                  "x": 143,
                  "y": 90
                },
                "relPosition": {
                  "x": 0,
                  "y": 76
                },
                "id": "IN1",
                "position": "left",
                "type": "target",
                "isConnectable": false,
                "style": {
                  "top": 76,
                  "left": 0
                }
              },
              {
                "glbPosition": {
                  "x": 143,
                  "y": 130
                },
                "relPosition": {
                  "x": 0,
                  "y": 116
                },
                "id": "IN2",
                "position": "left",
                "type": "target",
                "isConnectable": false,
                "style": {
                  "top": 116,
                  "left": 0
                }
              },
              {
                "glbPosition": {
                  "x": 233,
                  "y": 50
                },
                "relPosition": {
                  "x": 90,
                  "y": 36
                },
                "id": "ENO",
                "position": "right",
                "type": "source",
                "isConnectable": false,
                "style": {
                  "top": 36,
                  "right": 0
                }
              },
              {
                "glbPosition": {
                  "x": 233,
                  "y": 90
                },
                "relPosition": {
                  "x": 90,
                  "y": 76
                },
                "id": "OUT",
                "position": "right",
                "type": "source",
                "isConnectable": false,
                "style": {
                  "top": 76,
                  "right": 0
                }
              }
            ],
            "inputHandles": [
              {
                "glbPosition": {
                  "x": 143,
                  "y": 50
                },
                "relPosition": {
                  "x": 0,
                  "y": 36
                },
                "id": "EN",
                "position": "left",
                "type": "target",
                "isConnectable": false,
                "style": {
                  "top": 36,
                  "left": 0
                }
              },
              {
                "glbPosition": {
                  "x": 143,
                  "y": 90
                },
                "relPosition": {
                  "x": 0,
                  "y": 76
                },
                "id": "IN1",
                "position": "left",
                "type": "target",
                "isConnectable": false,
                "style": {
                  "top": 76,
                  "left": 0
                }
              },
              {
                "glbPosition": {
                  "x": 143,
                  "y": 130
                },
                "relPosition": {
                  "x": 0,
                  "y": 116
                },
                "id": "IN2",
                "position": "left",
                "type": "target",
                "isConnectable": false,
                "style": {
                  "top": 116,
                  "left": 0
                }
              }
            ],
            "outputHandles": [
              {
                "glbPosition": {
                  "x": 233,
                  "y": 50
                },
                "relPosition": {
                  "x": 90,
                  "y": 36
                },
                "id": "ENO",
                "position": "right",
                "type": "source",
                "isConnectable": false,
                "style": {
                  "top": 36,
                  "right": 0
                }
              },
              {
                "glbPosition": {
                  "x": 233,
                  "y": 90
                },
                "relPosition": {
                  "x": 90,
                  "y": 76
                },
                "id": "OUT",
                "position": "right",
                "type": "source",
                "isConnectable": false,
                "style": {
                  "top": 76,
                  "right": 0
                }
              }
            ],
            "inputConnector": {
              "glbPosition": {
                "x": 143,
                "y": 50
              },
              "relPosition": {
                "x": 0,
                "y": 36
              },
              "id": "EN",
              "position": "left",
              "type": "target",
              "isConnectable": false,
              "style": {
                "top": 36,
                "left": 0
              }
            },
            "outputConnector": {
              "glbPosition": {
                "x": 233,
                "y": 50
              },
              "relPosition": {
                "x": 90,
                "y": 36
              },
              "id": "ENO",
              "position": "right",
              "type": "source",
              "isConnectable": false,
              "style": {
                "top": 36,
                "right": 0
              }
            },
            "numericId": "609728",
            "variant": {
              "name": "GT",
              "type": "function",
              "language": "st",
              "variables": [
                {
                  "name": "EN",
                  "class": "input",
                  "type": {
                    "definition": "base-type",
                    "value": "BOOL"
                  }
                },
                {
                  "name": "ENO",
                  "class": "output",
                  "type": {
                    "definition": "base-type",
                    "value": "BOOL"
                  }
                },
                {
                  "name": "OUT",
                  "class": "output",
                  "type": {
                    "definition": "base-type",
                    "value": "BOOL"
                  }
                },
                {
                  "name": "IN1",
                  "class": "input",
                  "type": {
                    "definition": "generic-type",
                    "value": "ANY"
                  }
                },
                {
                  "name": "IN2",
                  "class": "input",
                  "type": {
                    "definition": "generic-type",
                    "value": "ANY"
                  }
                }
              ],
              "body": "Greater Than",
              "documentation": "(IN1: ANY, IN2: ANY) => OUT:BOOL",
              "extensible": true
            },
            "variable": {
              "name": ""
            },
            "executionOrder": 0,
            "executionControl": true,
            "lockExecutionControl": false,
            "connectedVariables": [
              {
                "handleId": "IN2",
                "type": "input",
                "variable": {
                  "name": "MaxLimitTemp",
                  "class": "global",
                  "type": {
                    "definition": "base-type",
                    "value": "int"
                  },
                  "location": "%MW1",
                  "initialValue": null,
                  "documentation": "",
                  "debug": false
                }
              },
              {
                "handleId": "OUT",
                "type": "output",
                "variable": {
                  "name": "CoolingPumpStatus",
                  "class": "global",
                  "type": {
                    "definition": "base-type",
                    "value": "BOOL"
                  },
                  "location": "%QX0.0",
                  "initialValue": null,
                  "documentation": "",
                  "debug": false
                }
              },
              {
                "handleId": "IN1",
                "type": "input",
                "variable": {
                  "name": "CurrentTemp",
                  "class": "local",
                  "type": {
                    "definition": "base-type",
                    "value": "int"
                  },
                  "location": "%MW0",
                  "initialValue": "0",
                  "documentation": "Nhiệt độ hiện tại",
                  "debug": false
                }
              }
            ],
            "draggable": true,
            "selectable": true,
            "deletable": true
          }
        },
        {
          "id": "right-rail-rung_main_c8567ade-943a-4062-8b88-d21c20d95ff3",
          "type": "powerRail",
          "position": {
            "x": 493,
            "y": 30
          },
          "height": 40,
          "width": 3,
          "measured": {
            "width": 3,
            "height": 40
          },
          "draggable": false,
          "selectable": false,
          "data": {
            "handles": [
              {
                "glbPosition": {
                  "x": 297,
                  "y": 50
                },
                "relPosition": {
                  "x": 3,
                  "y": 20
                },
                "id": "right-rail",
                "position": "left",
                "type": "target",
                "isConnectable": false,
                "style": {
                  "top": 20,
                  "left": -3
                },
                "x": 493
              }
            ],
            "inputHandles": [
              {
                "glbPosition": {
                  "x": 297,
                  "y": 50
                },
                "relPosition": {
                  "x": 3,
                  "y": 20
                },
                "id": "right-rail",
                "position": "left",
                "type": "target",
                "isConnectable": false,
                "style": {
                  "top": 20,
                  "left": -3
                }
              }
            ],
            "outputHandles": [],
            "inputConnector": {
              "glbPosition": {
                "x": 297,
                "y": 50
              },
              "relPosition": {
                "x": 3,
                "y": 20
              },
              "id": "right-rail",
              "position": "left",
              "type": "target",
              "isConnectable": false,
              "style": {
                "top": 20,
                "left": -3
              }
            },
            "numericId": "4608163",
            "variant": "right",
            "variable": {
              "name": ""
            },
            "executionOrder": 0,
            "draggable": false,
            "selectable": false,
            "deletable": false,
            "hasDivergence": false
          }
        },
        {
          "id": "VARIABLE_c5b3d9b8-7748-4e7c-bc62-aadb40bd04cc",
          "type": "variable",
          "position": {
            "x": 33,
            "y": 74
          },
          "height": 32,
          "width": 80,
          "measured": {
            "width": 80,
            "height": 32
          },
          "draggable": false,
          "selectable": true,
          "data": {
            "handles": [
              {
                "glbPosition": {
                  "x": 193,
                  "y": 90
                },
                "relPosition": {
                  "x": 80,
                  "y": 16
                },
                "id": "output",
                "position": "right",
                "isConnectable": false,
                "type": "source"
              }
            ],
            "inputHandles": [],
            "outputHandles": [
              {
                "glbPosition": {
                  "x": 193,
                  "y": 90
                },
                "relPosition": {
                  "x": 80,
                  "y": 16
                },
                "id": "output",
                "position": "right",
                "isConnectable": false,
                "type": "source"
              }
            ],
            "outputConnector": {
              "glbPosition": {
                "x": 193,
                "y": 90
              },
              "relPosition": {
                "x": 80,
                "y": 16
              },
              "id": "output",
              "position": "right",
              "isConnectable": false,
              "type": "source"
            },
            "numericId": "1828198",
            "variable": {
              "name": "CurrentTemp",
              "class": "local",
              "type": {
                "definition": "base-type",
                "value": "int"
              },
              "location": "%MW0",
              "initialValue": "0",
              "documentation": "Nhiệt độ hiện tại",
              "debug": false
            },
            "executionOrder": 0,
            "variant": "input",
            "block": {
              "id": "BLOCK_9e0ffea3-93df-4fd7-a930-d6b7a312d96d",
              "handleId": "IN1",
              "variableType": {
                "name": "IN1",
                "class": "input",
                "type": {
                  "definition": "generic-type",
                  "value": "ANY"
                }
              }
            },
            "draggable": false,
            "selectable": true,
            "deletable": false,
            "wrongVariable": true
          }
        },
        {
          "id": "VARIABLE_baed7663-4317-43c6-87e2-436c7a0d7359",
          "type": "variable",
          "position": {
            "x": 33,
            "y": 114
          },
          "height": 32,
          "width": 80,
          "measured": {
            "width": 80,
            "height": 32
          },
          "draggable": false,
          "selectable": true,
          "data": {
            "handles": [
              {
                "glbPosition": {
                  "x": 193,
                  "y": 130
                },
                "relPosition": {
                  "x": 80,
                  "y": 16
                },
                "id": "output",
                "position": "right",
                "isConnectable": false,
                "type": "source"
              }
            ],
            "inputHandles": [],
            "outputHandles": [
              {
                "glbPosition": {
                  "x": 193,
                  "y": 130
                },
                "relPosition": {
                  "x": 80,
                  "y": 16
                },
                "id": "output",
                "position": "right",
                "isConnectable": false,
                "type": "source"
              }
            ],
            "outputConnector": {
              "glbPosition": {
                "x": 193,
                "y": 130
              },
              "relPosition": {
                "x": 80,
                "y": 16
              },
              "id": "output",
              "position": "right",
              "isConnectable": false,
              "type": "source"
            },
            "numericId": "6249992",
            "variable": {
              "name": "MaxLimitTemp",
              "class": "local",
              "type": {
                "definition": "base-type",
                "value": "int"
              },
              "location": "%MW1",
              "initialValue": "50",
              "documentation": "Giới hạn tối đa trước khi phải bật máy bơm",
              "debug": true,
              "id": "broken-VARIABLE_baed7663-4317-43c6-87e2-436c7a0d7359"
            },
            "executionOrder": 0,
            "variant": "input",
            "block": {
              "id": "BLOCK_9e0ffea3-93df-4fd7-a930-d6b7a312d96d",
              "handleId": "IN2",
              "variableType": {
                "name": "IN2",
                "class": "input",
                "type": {
                  "definition": "generic-type",
                  "value": "ANY"
                }
              }
            },
            "draggable": false,
            "selectable": true,
            "deletable": false,
            "wrongVariable": true
          }
        },
        {
          "id": "VARIABLE_f05a9e22-26b2-4ffd-a0c4-c7b976ac1e39",
          "type": "variable",
          "position": {
            "x": 263,
            "y": 74
          },
          "height": 32,
          "width": 80,
          "measured": {
            "width": 80,
            "height": 32
          },
          "draggable": false,
          "selectable": true,
          "data": {
            "handles": [
              {
                "glbPosition": {
                  "x": 263,
                  "y": 90
                },
                "relPosition": {
                  "x": 0,
                  "y": 16
                },
                "id": "input",
                "position": "left",
                "isConnectable": false,
                "type": "target"
              }
            ],
            "inputHandles": [
              {
                "glbPosition": {
                  "x": 263,
                  "y": 90
                },
                "relPosition": {
                  "x": 0,
                  "y": 16
                },
                "id": "input",
                "position": "left",
                "isConnectable": false,
                "type": "target"
              }
            ],
            "outputHandles": [],
            "inputConnector": {
              "glbPosition": {
                "x": 263,
                "y": 90
              },
              "relPosition": {
                "x": 0,
                "y": 16
              },
              "id": "input",
              "position": "left",
              "isConnectable": false,
              "type": "target"
            },
            "numericId": "1649186",
            "variable": {
              "name": "CoolingPumpStatus",
              "class": "local",
              "type": {
                "definition": "base-type",
                "value": "bool"
              },
              "location": "%QX0.0",
              "initialValue": null,
              "documentation": "Trạng thái bật tắt máy bơm",
              "debug": true,
              "id": "broken-VARIABLE_f05a9e22-26b2-4ffd-a0c4-c7b976ac1e39"
            },
            "executionOrder": 0,
            "variant": "output",
            "block": {
              "id": "BLOCK_9e0ffea3-93df-4fd7-a930-d6b7a312d96d",
              "handleId": "OUT",
              "variableType": {
                "name": "OUT",
                "class": "output",
                "type": {
                  "definition": "base-type",
                  "value": "BOOL"
                }
              }
            },
            "draggable": false,
            "selectable": true,
            "deletable": false,
            "wrongVariable": true
          }
        }
      ],
      "edges": [
        {
          "id": "e_left-rail-rung_main_c8567ade-943a-4062-8b88-d21c20d95ff3_BLOCK_9e0ffea3-93df-4fd7-a930-d6b7a312d96d__left-rail_IN1",
          "source": "left-rail-rung_main_c8567ade-943a-4062-8b88-d21c20d95ff3",
          "sourceHandle": "left-rail",
          "target": "BLOCK_9e0ffea3-93df-4fd7-a930-d6b7a312d96d",
          "targetHandle": "EN"
        },
        {
          "id": "e_BLOCK_9e0ffea3-93df-4fd7-a930-d6b7a312d96d_right-rail-rung_main_c8567ade-943a-4062-8b88-d21c20d95ff3__OUT_right-rail",
          "source": "BLOCK_9e0ffea3-93df-4fd7-a930-d6b7a312d96d",
          "sourceHandle": "ENO",
          "target": "right-rail-rung_main_c8567ade-943a-4062-8b88-d21c20d95ff3",
          "targetHandle": "right-rail"
        },
        {
          "id": "e_VARIABLE_c5b3d9b8-7748-4e7c-bc62-aadb40bd04cc_BLOCK_9e0ffea3-93df-4fd7-a930-d6b7a312d96d__output_IN1",
          "source": "VARIABLE_c5b3d9b8-7748-4e7c-bc62-aadb40bd04cc",
          "sourceHandle": "output",
          "target": "BLOCK_9e0ffea3-93df-4fd7-a930-d6b7a312d96d",
          "targetHandle": "IN1"
        },
        {
          "id": "e_VARIABLE_baed7663-4317-43c6-87e2-436c7a0d7359_BLOCK_9e0ffea3-93df-4fd7-a930-d6b7a312d96d__output_IN2",
          "source": "VARIABLE_baed7663-4317-43c6-87e2-436c7a0d7359",
          "sourceHandle": "output",
          "target": "BLOCK_9e0ffea3-93df-4fd7-a930-d6b7a312d96d",
          "targetHandle": "IN2"
        },
        {
          "id": "e_BLOCK_9e0ffea3-93df-4fd7-a930-d6b7a312d96d_VARIABLE_f05a9e22-26b2-4ffd-a0c4-c7b976ac1e39__OUT_input",
          "source": "BLOCK_9e0ffea3-93df-4fd7-a930-d6b7a312d96d",
          "sourceHandle": "OUT",
          "target": "VARIABLE_f05a9e22-26b2-4ffd-a0c4-c7b976ac1e39",
          "targetHandle": "input"
        }
      ]
    }
  ]
}
END_PROGRAM