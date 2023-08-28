class Rich:
    def __init__(self, **kwargs):
        self.img_pc = kwargs.get('img_url_pc')
        self.img_mobile = kwargs.get('img_url_mobile')
        self.name = kwargs.get('name')
        self.breathe = kwargs.get('breathe')
        
    def create_rich(self) -> dict:
        return str({
                      "content": [
                        {
                          "widgetName": "raShowcase",
                          "type": "billboard",
                          "blocks": [
                            {
                              "imgLink": "",
                              "img": {
                                "src": self.img_pc,
                                "srcMobile": self.img_mobile,
                                "alt": self.name,
                                "position": "width_full",
                                "positionMobile": "width_full"
                              },
                              "title": {
                                "content": self.name[0],
                                "size": "size4",
                                "align": "center",
                                "color": "color1"
                              },
                              "text": {
                                "size": "size2",
                                "align": "left",
                                "color": "color2",
                                "content": [
                                  self.breathe[0]
                                ]
                              }
                            }
                          ]
                        }
                      ],
                      "version": 0.3
                    })
