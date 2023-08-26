class Rich:

    def __init__(self, **kwargs):
        ...
        img_pc = kwargs.get('img-url-pc')
        img_mobile = kwargs.get('img-url-mobile')
        name = kwargs.get('name')
        description = kwargs.get('description')

        self.pattern_1 = {
                      "content": [
                        {
                          "widgetName": "raShowcase",
                          "type": "billboard",
                          "blocks": [
                            {
                              "imgLink": "",
                              "img": {
                                "src": img_pc,
                                "srcMobile": img_mobile,
                                "alt": name,
                                "position": "width_full",
                                "positionMobile": "width_full"
                              },
                              "title": {
                                "content": [
                                  name
                                ],
                                "size": "size4",
                                "align": "center",
                                "color": "color1"
                              },
                              "text": {
                                "size": "size2",
                                "align": "left",
                                "color": "color2",
                                "content": [
                                  description
                                ]
                              }
                            }
                          ]
                        }
                      ],
                      "version": 0.3
                    }