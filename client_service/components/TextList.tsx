import { useEffect, useState } from 'react';
import { Card, Image, Text, Button, Flex } from '@mantine/core';
import axios from 'axios';
import {useRouter} from "next/router";

interface TextItem {
  id: number;
  title: string;
  description: string;
  fanfic_text: string;
  pic: string;
}

const TextList = () => {
  const [texts, setTexts] = useState<TextItem[]>([]);
  const router = useRouter();




  const handleTextClick = (id: number) => {
    router.push(`/text/${id}`);
  };

  useEffect(() => {
    const fetchData = async () => {
      let id = 1;
      const fetchedTexts: TextItem[] = [];

      while (true) {
        try {
          const response = await axios.get(`http://localhost:8000/get_text/${id}`);
          const data = response.data;
          if (!data) break;

          fetchedTexts.push(data);
          id++;
        } catch (error) {
          console.error('Error fetching texts:', error);
          break;
        }
      }

      setTexts(fetchedTexts);
    };

    fetchData();
  }, []);

  const convertBase64ToImage = (base64String: string) => {
    return `data:image/jpeg;base64,${base64String}`;
  };



  return (
    <div>
      <Flex>
        {texts.map(text => (
          <Card key={text.id} shadow="sm" padding="lg" radius="md" withBorder>
            <Card.Section>
              <Image
                src={convertBase64ToImage(text.pic)}
                height={160}
                alt={text.title}
              />
            </Card.Section>

            <Text size="sm" c="dimmed">
              {text.description}
            </Text>

            <Button
              color="blue"
              fullWidth
              mt="md"
              radius="md"
              onClick={() => handleTextClick(text.id)}
            >
              Открыть
            </Button>
          </Card>
        ))}
      </Flex>
    </div>
  );
};

export default TextList;
